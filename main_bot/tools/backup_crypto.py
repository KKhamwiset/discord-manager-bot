"""Offline key and recovery CLI for encrypted Mochi Bot backups.

Examples (from the repository root)::

    python -m main_bot.tools.backup_crypto generate --private-key <outside-repo>/backup.key --public-key <outside-repo>/backup.pub
    python -m main_bot.tools.backup_crypto inspect <outside-repo>/backup.mbak
    python -m main_bot.tools.backup_crypto decrypt <outside-repo>/backup.mbak --private-key <outside-repo>/backup.key --expected-sha256 <trusted-discord-sha256> --output <outside-repo>/backup.zip
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import sys
import tempfile
import uuid
import zipfile
from pathlib import Path

try:  # Supports ``python -m tools.backup_crypto`` from main_bot/.
    from backup_crypto import (
        BackupCryptoError,
        decrypt_file,
        encode_key_base64,
        generate_keypair,
        inspect_envelope,
        key_fingerprint,
        load_private_key_base64,
    )
except ImportError:  # Supports repository-root module invocation.
    from main_bot.backup_crypto import (
        BackupCryptoError,
        decrypt_file,
        encode_key_base64,
        generate_keypair,
        inspect_envelope,
        key_fingerprint,
        load_private_key_base64,
    )


def _ensure_new_file(path: Path) -> None:
    if os.path.lexists(path):
        raise FileExistsError(path)
    if not path.parent.is_dir():
        raise FileNotFoundError(path.parent)


def _write_secret(path: Path, value: str) -> None:
    with path.open("x", encoding="ascii", newline="\n") as stream:
        os.chmod(path, 0o600)
        stream.write(value)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def _generate(args: argparse.Namespace) -> int:
    private_path = Path(args.private_key).expanduser().resolve()
    public_path = Path(args.public_key).expanduser().resolve()
    if private_path == public_path:
        raise ValueError("private and public key paths must differ")
    _ensure_new_file(private_path)
    _ensure_new_file(public_path)
    private_key, public_key = generate_keypair()
    private_created = False
    try:
        _write_secret(private_path, encode_key_base64(private_key))
        private_created = True
        _write_secret(public_path, encode_key_base64(public_key))
    except BaseException:
        if private_created:
            try:
                private_path.unlink()
            except FileNotFoundError:
                pass
        try:
            public_path.unlink()
        except FileNotFoundError:
            pass
        raise
    print("Generated an X25519 backup key pair.")
    print(f"Private key file: {private_path}")
    print(f"Public key file: {public_path}")
    print(f"Key ID: {key_fingerprint(public_key)}")
    return 0


def _inspect(args: argparse.Namespace) -> int:
    metadata = inspect_envelope(Path(args.envelope))
    print(json.dumps(metadata, indent=2, sort_keys=True))
    return 0


_SHA256 = re.compile(r"[0-9a-fA-F]{64}", re.ASCII)


def _stage_verified_ciphertext(source: Path, destination: Path, expected_sha256: str) -> str:
    """Hash and copy one opened ciphertext stream, then pin that exact copy."""

    if _SHA256.fullmatch(expected_sha256) is None:
        raise BackupCryptoError("expected ciphertext SHA-256 must be exactly 64 hexadecimal characters")
    expected = expected_sha256.lower()
    digest = hashlib.sha256()
    try:
        with source.open("rb") as opened_ciphertext, destination.open("xb") as staged_ciphertext:
            os.chmod(destination, 0o600)
            for chunk in iter(lambda: opened_ciphertext.read(1024 * 1024), b""):
                digest.update(chunk)
                staged_ciphertext.write(chunk)
            staged_ciphertext.flush()
            os.fsync(staged_ciphertext.fileno())
        actual = digest.hexdigest()
        if not hmac.compare_digest(actual, expected):
            raise BackupCryptoError("ciphertext SHA-256 does not match the trusted Discord message")
        return actual
    except BaseException:
        try:
            destination.unlink()
        except FileNotFoundError:
            pass
        raise


def _validate_backup_zip(path: Path) -> None:
    try:
        with zipfile.ZipFile(path, "r") as archive:
            if "manifest.json" not in archive.namelist():
                raise BackupCryptoError("decrypted ZIP has no manifest")
            if archive.testzip() is not None:
                raise BackupCryptoError("decrypted ZIP failed integrity validation")
            try:
                manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError, KeyError) as exc:
                raise BackupCryptoError("decrypted ZIP manifest is invalid") from exc
            if not isinstance(manifest, dict) or manifest.get("format") != "mochi-mongodb-backup":
                raise BackupCryptoError("decrypted ZIP manifest is invalid")
    except zipfile.BadZipFile as exc:
        raise BackupCryptoError("authenticated payload is not a valid ZIP") from exc


def _decrypt(args: argparse.Namespace) -> int:
    envelope_path = Path(args.envelope).expanduser().resolve()
    private_path = Path(args.private_key).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    _ensure_new_file(output_path)
    encoded_key = private_path.read_bytes()
    if len(encoded_key) > 4096:
        raise BackupCryptoError("private key file is invalid")
    private_key = load_private_key_base64(encoded_key)
    with tempfile.TemporaryDirectory(prefix="mochi-recovery-", dir=output_path.parent) as temporary:
        temporary_directory = Path(temporary)
        os.chmod(temporary_directory, 0o700)
        staged_envelope = temporary_directory / "digest-verified.mbak"
        verified_digest = _stage_verified_ciphertext(
            envelope_path,
            staged_envelope,
            args.expected_sha256,
        )
        temporary_output = temporary_directory / f"{uuid.uuid4().hex}.aead-verified.zip"
        metadata = decrypt_file(staged_envelope, temporary_output, private_key)
        _validate_backup_zip(temporary_output)
        if os.path.lexists(output_path):
            raise FileExistsError(output_path)
        os.replace(temporary_output, output_path)
        os.chmod(output_path, 0o600)
    print("Trusted ciphertext SHA-256 matched; secretstream AEAD frame integrity verified.")
    print("Sender identity depends on the trusted Discord digest provenance, not the public-key envelope alone.")
    print(f"Backup ID: {metadata['backup_id']}")
    print(f"Key ID: {metadata['key_id']}")
    print(f"Ciphertext SHA-256: {verified_digest}")
    print(f"ZIP file: {output_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage Mochi Bot encrypted backup keys and envelopes.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="Generate an X25519 backup key pair.")
    generate.add_argument("--private-key", required=True, help="New file for the base64 private key.")
    generate.add_argument("--public-key", required=True, help="New file for the base64 public key.")
    generate.set_defaults(handler=_generate)

    inspect = subparsers.add_parser("inspect", help="Inspect public envelope metadata (not authenticated).")
    inspect.add_argument("envelope", help="Encrypted .mbak file.")
    inspect.set_defaults(handler=_inspect)

    decrypt = subparsers.add_parser(
        "decrypt",
        help="Pin a trusted ciphertext digest, verify AEAD integrity, and recover a backup ZIP.",
    )
    decrypt.add_argument("envelope", help="Encrypted .mbak file.")
    decrypt.add_argument("--private-key", required=True, help="Base64 private key file.")
    decrypt.add_argument(
        "--expected-sha256",
        required=True,
        help="Ciphertext SHA-256 copied from the trusted bot-authored Discord message.",
    )
    decrypt.add_argument("--output", required=True, help="New destination ZIP file.")
    decrypt.set_defaults(handler=_decrypt)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (BackupCryptoError, OSError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    sys.exit(main())
