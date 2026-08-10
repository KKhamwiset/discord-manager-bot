"""Encrypted, all-or-nothing MongoDB backups for Mochi Bot."""

from __future__ import annotations

import asyncio
import datetime as dt
import hashlib
import json
import logging
import os
import re
import tempfile
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import discord
from discord.ext import commands, tasks

try:  # ``python main.py`` is run from main_bot/ in production.
    from backup_crypto import KeyConfigurationError, encrypt_file, key_fingerprint, load_public_key_base64
except ImportError:  # Tests import the cog through the repository namespace.
    from main_bot.backup_crypto import (
        KeyConfigurationError,
        encrypt_file,
        key_fingerprint,
        load_public_key_base64,
    )


logger = logging.getLogger(__name__)
UTC_PLUS_SEVEN = dt.timezone(dt.timedelta(hours=7))
MANIFEST_FORMAT = "mochi-mongodb-backup"
MANIFEST_VERSION = 1
_CHANNEL_ID = re.compile(r"[0-9]+", re.ASCII)


class BackupFailure(Exception):
    """An operational backup failure represented by a non-sensitive code."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class CollectionExport:
    name: str
    archive_name: str
    source_count: int
    exported_count: int
    byte_count: int
    sha256: str
    path: Path


@dataclass(frozen=True)
class BackupResult:
    backup_id: str
    created_at: str
    key_id: str
    collection_count: int
    source_count: int
    exported_count: int
    ciphertext_bytes: int
    ciphertext_sha256: str


def backup_enabled_from_env(value: str | None = None) -> bool:
    """Return whether scheduled backups were explicitly enabled.

    A missing value is intentionally false.  Manual owner-only backups do not
    use this flag.
    """

    if value is None:
        value = os.getenv("BACKUP_ENABLED")
    return value is not None and value.strip().lower() in {"1", "true", "yes", "on"}


def _utc_timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_mongoexport_config(path: Path, mongo_uri: str) -> None:
    """Write a restrictive YAML config without exposing credentials in argv."""

    # A JSON string literal is valid YAML and safely quotes punctuation,
    # whitespace, fragments, and query parameters in MongoDB URIs.
    payload = f"uri: {json.dumps(mongo_uri, ensure_ascii=True)}\n".encode("utf-8")
    try:
        with path.open("xb") as config:
            os.chmod(path, 0o600)
            config.write(payload)
            config.flush()
            os.fsync(config.fileno())
    except OSError as exc:
        raise BackupFailure("mongoexport-config-failed") from exc


def _safe_collection_names(names: Iterable[Any]) -> list[str]:
    selected = list(names)
    if any(not isinstance(name, str) or not name or "\x00" in name for name in selected):
        raise BackupFailure("invalid-collection-list")
    if len(set(selected)) != len(selected):
        raise BackupFailure("invalid-collection-list")
    return sorted(selected)


def _normalize_and_validate_export(path: Path, source_count: int) -> tuple[int, int, str]:
    if not path.is_file():
        raise BackupFailure("missing-export-output")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise BackupFailure("unreadable-export-output") from exc
    if not raw.strip():
        if source_count != 0:
            raise BackupFailure("export-count-mismatch")
        documents: object = []
    else:
        try:
            documents = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise BackupFailure("invalid-export-output") from exc
    if not isinstance(documents, list):
        raise BackupFailure("invalid-export-output")
    exported_count = len(documents)
    if exported_count != source_count:
        raise BackupFailure("export-count-mismatch")
    normalized = json.dumps(
        documents,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    try:
        path.write_bytes(normalized)
        os.chmod(path, 0o600)
    except OSError as exc:
        raise BackupFailure("unwritable-export-output") from exc
    return exported_count, len(normalized), hashlib.sha256(normalized).hexdigest()


def _build_zip(
    zip_path: Path,
    *,
    backup_id: str,
    created_at: str,
    database_name: str,
    exports: list[CollectionExport],
) -> None:
    source_total = sum(item.source_count for item in exports)
    exported_total = sum(item.exported_count for item in exports)
    manifest = {
        "format": MANIFEST_FORMAT,
        "format_version": MANIFEST_VERSION,
        "backup_id": backup_id,
        "created_at": created_at,
        "database": {"name": database_name},
        "collections": [
            {
                "name": item.name,
                "file": item.archive_name,
                "source_count": item.source_count,
                "exported_count": item.exported_count,
                "bytes": item.byte_count,
                "sha256": item.sha256,
            }
            for item in exports
        ],
        "totals": {
            "collections": len(exports),
            "source_documents": source_total,
            "exported_documents": exported_total,
            "collection_bytes": sum(item.byte_count for item in exports),
        },
    }
    manifest_bytes = json.dumps(
        manifest,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    try:
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            archive.writestr("manifest.json", manifest_bytes)
            for item in exports:
                archive.write(item.path, arcname=item.archive_name)
        os.chmod(zip_path, 0o600)
    except (OSError, zipfile.BadZipFile) as exc:
        raise BackupFailure("archive-creation-failed") from exc


class Backup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._backup_lock = asyncio.Lock()
        self._scheduled_enabled = backup_enabled_from_env()

    async def cog_load(self) -> None:
        if (
            self._scheduled_enabled
            and getattr(self.bot, "instance", None) == "server"
            and not self.backup_task.is_running()
        ):
            self.backup_task.start()

    async def cog_unload(self) -> None:
        if self.backup_task.is_running():
            self.backup_task.cancel()

    @tasks.loop(time=dt.time(hour=0, minute=0, tzinfo=UTC_PLUS_SEVEN))
    async def backup_task(self) -> None:
        # An unexpected failure must not terminate discord.py's loop and
        # suppress all future scheduled backups.
        try:
            await self.run_backup()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("Scheduled backup iteration failed (type=%s)", type(exc).__name__)

    async def _resolve_channel(self) -> Any:
        raw_channel_id = os.getenv("BACKUP_CHANNEL_ID")
        if raw_channel_id is None or _CHANNEL_ID.fullmatch(raw_channel_id.strip()) is None:
            raise BackupFailure("invalid-backup-channel")
        channel_id = int(raw_channel_id.strip())
        if channel_id <= 0 or channel_id > (2**64 - 1):
            raise BackupFailure("invalid-backup-channel")

        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception as exc:
                raise BackupFailure("backup-channel-unavailable") from exc
        guild = getattr(channel, "guild", None)
        if guild is None or not callable(getattr(channel, "send", None)):
            raise BackupFailure("invalid-backup-channel")

        member = getattr(guild, "me", None)
        if member is None:
            bot_user = getattr(self.bot, "user", None)
            get_member = getattr(guild, "get_member", None)
            if bot_user is not None and callable(get_member):
                member = get_member(bot_user.id)
        permissions_for = getattr(channel, "permissions_for", None)
        if member is None or not callable(permissions_for):
            raise BackupFailure("backup-channel-permissions-unavailable")
        try:
            permissions = permissions_for(member)
        except Exception as exc:
            raise BackupFailure("backup-channel-permissions-unavailable") from exc
        is_thread = isinstance(channel, discord.Thread)
        send_allowed = (
            getattr(permissions, "send_messages_in_threads", False)
            if is_thread
            else getattr(permissions, "send_messages", False)
        )
        if not send_allowed or not getattr(permissions, "attach_files", False):
            raise BackupFailure("backup-channel-permission-denied")
        return channel

    async def _export_collection(
        self,
        *,
        collection_name: str,
        ordinal: int,
        directory: Path,
        mongoexport_config: Path,
        database_name: str,
    ) -> CollectionExport:
        archive_name = f"collections/collection_{ordinal:06d}.json"
        output_path = directory / f"collection_{ordinal:06d}.json"
        try:
            source_count = await self.bot.db[collection_name].count_documents({})
        except Exception as exc:
            raise BackupFailure("source-count-failed") from exc
        if not isinstance(source_count, int) or isinstance(source_count, bool) or source_count < 0:
            raise BackupFailure("invalid-source-count")
        try:
            process = await asyncio.create_subprocess_exec(
                "mongoexport",
                "--config",
                str(mongoexport_config),
                "--db",
                database_name,
                "--collection",
                collection_name,
                "--out",
                str(output_path),
                "--jsonArray",
                "--pretty",
                "--jsonFormat=canonical",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError as exc:
            raise BackupFailure("mongoexport-unavailable") from exc
        except OSError as exc:
            raise BackupFailure("mongoexport-start-failed") from exc
        try:
            await process.communicate()
        except BaseException:
            if process.returncode is None:
                process.kill()
                await process.wait()
            raise
        if process.returncode != 0:
            raise BackupFailure("mongoexport-failed")
        exported_count, byte_count, digest = await asyncio.to_thread(
            _normalize_and_validate_export,
            output_path,
            source_count,
        )
        return CollectionExport(
            name=collection_name,
            archive_name=archive_name,
            source_count=source_count,
            exported_count=exported_count,
            byte_count=byte_count,
            sha256=digest,
            path=output_path,
        )

    async def _perform_backup(self) -> BackupResult:
        raw_public_key = os.getenv("BACKUP_ENCRYPTION_PUBLIC_KEY")
        if raw_public_key is None:
            raise BackupFailure("encryption-key-unavailable")
        try:
            public_key = load_public_key_base64(raw_public_key)
        except (KeyConfigurationError, UnicodeError) as exc:
            raise BackupFailure("encryption-key-invalid") from exc

        channel = await self._resolve_channel()
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            raise BackupFailure("database-connection-unavailable")
        database_name = getattr(self.bot.db, "name", None)
        if not isinstance(database_name, str) or not database_name:
            raise BackupFailure("database-name-unavailable")

        backup_id = str(uuid.uuid4())
        created_at = _utc_timestamp()
        key_id = key_fingerprint(public_key)
        with tempfile.TemporaryDirectory(prefix="mochi-backup-") as temporary:
            temporary_path = Path(temporary)
            os.chmod(temporary_path, 0o700)
            mongoexport_config = temporary_path / "mongoexport-config.yaml"
            _write_mongoexport_config(mongoexport_config, mongo_uri)
            try:
                collection_names = _safe_collection_names(await self.bot.db.list_collection_names())
            except BackupFailure:
                raise
            except Exception as exc:
                raise BackupFailure("collection-list-failed") from exc

            exports: list[CollectionExport] = []
            for ordinal, collection_name in enumerate(collection_names, start=1):
                exports.append(
                    await self._export_collection(
                        collection_name=collection_name,
                        ordinal=ordinal,
                        directory=temporary_path,
                        mongoexport_config=mongoexport_config,
                        database_name=database_name,
                    )
                )

            zip_path = temporary_path / "backup.zip"
            await asyncio.to_thread(
                _build_zip,
                zip_path,
                backup_id=backup_id,
                created_at=created_at,
                database_name=database_name,
                exports=exports,
            )
            encrypted_path = temporary_path / f"{backup_id}.mbak"
            await asyncio.to_thread(
                encrypt_file,
                zip_path,
                encrypted_path,
                public_key,
                backup_id=backup_id,
                created_at=created_at,
            )
            ciphertext_bytes = encrypted_path.stat().st_size
            ciphertext_sha256 = await asyncio.to_thread(_sha256_file, encrypted_path)
            filesize_limit = getattr(getattr(channel, "guild", None), "filesize_limit", None)
            if not isinstance(filesize_limit, int) or isinstance(filesize_limit, bool) or filesize_limit <= 0:
                raise BackupFailure("attachment-limit-unavailable")
            if ciphertext_bytes > filesize_limit:
                raise BackupFailure("encrypted-backup-too-large")

            source_total = sum(item.source_count for item in exports)
            exported_total = sum(item.exported_count for item in exports)
            message = (
                "Encrypted Mochi backup\n"
                f"Backup ID: `{backup_id}`\n"
                f"Created: `{created_at}`\n"
                f"Key ID: `{key_id}`\n"
                f"Collections: {len(exports)}\n"
                f"Source documents: {source_total}\n"
                f"Exported documents: {exported_total}\n"
                f"Ciphertext bytes: {ciphertext_bytes}\n"
                f"Ciphertext SHA-256: `{ciphertext_sha256}`"
            )
            attachment = discord.File(
                str(encrypted_path),
                filename=f"mochi-backup-{backup_id}.mbak",
            )
            try:
                await channel.send(message, file=attachment)
            except Exception as exc:
                raise BackupFailure("backup-upload-failed") from exc
            finally:
                attachment.close()

        return BackupResult(
            backup_id=backup_id,
            created_at=created_at,
            key_id=key_id,
            collection_count=len(exports),
            source_count=source_total,
            exported_count=exported_total,
            ciphertext_bytes=ciphertext_bytes,
            ciphertext_sha256=ciphertext_sha256,
        )

    async def _send_context_status(self, ctx: commands.Context | None, message: str) -> None:
        if ctx is None:
            return
        try:
            await ctx.send(message)
        except Exception:
            logger.warning("Unable to send manual backup status")

    async def run_backup(self, ctx: commands.Context | None = None) -> BackupResult | None:
        if self._backup_lock.locked():
            await self._send_context_status(ctx, "A backup is already running.")
            return None
        await self._backup_lock.acquire()
        try:
            try:
                result = await self._perform_backup()
            except BackupFailure as exc:
                logger.error("Backup failed (code=%s)", exc.code)
                await self._send_context_status(ctx, f"Backup failed ({exc.code}).")
                return None
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error("Backup failed (type=%s)", type(exc).__name__)
                await self._send_context_status(ctx, "Backup failed (unexpected-error).")
                return None
            logger.info(
                "Encrypted backup completed (backup_id=%s key_id=%s collections=%d documents=%d bytes=%d sha256=%s)",
                result.backup_id,
                result.key_id,
                result.collection_count,
                result.exported_count,
                result.ciphertext_bytes,
                result.ciphertext_sha256,
            )
            await self._send_context_status(
                ctx,
                f"Encrypted backup completed. Backup ID: `{result.backup_id}`.",
            )
            return result
        finally:
            self._backup_lock.release()

    @commands.command(name="backup", help="Manually trigger an encrypted database backup")
    @commands.is_owner()
    async def manual_backup(self, ctx: commands.Context) -> None:
        # Intentionally independent of BACKUP_ENABLED.
        await self.run_backup(ctx)

    @backup_task.before_loop
    async def before_backup_task(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Backup(bot))
