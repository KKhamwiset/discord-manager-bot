"""Streaming encryption helpers for Mochi Bot database backups.

The v1 envelope deliberately contains only non-sensitive routing metadata.  The
ZIP payload, including database and collection names, is encrypted with a
random secretstream key which is sealed to an X25519 public key.  Public-key
encryption provides recipient confidentiality and frame integrity, not sender
identity; recovery must separately verify the bot-published ciphertext digest.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import struct
import uuid
from pathlib import Path
from typing import BinaryIO, Mapping

from nacl import bindings
from nacl.exceptions import CryptoError
from nacl.public import PrivateKey, PublicKey, SealedBox


MAGIC = b"MOCHI-MBAK"
FORMAT_NAME = "mochi-backup-envelope"
FORMAT_VERSION = 1
DEFAULT_CHUNK_SIZE = 64 * 1024
MAX_CHUNK_SIZE = 8 * 1024 * 1024
MAX_HEADER_SIZE = 64 * 1024
_U32 = struct.Struct(">I")
_U16 = struct.Struct(">H")
_KEY_ID_PREFIX = "sha256:"


class BackupCryptoError(Exception):
    """Base class for safe-to-handle backup cryptography failures."""


class KeyConfigurationError(BackupCryptoError):
    """Raised when a configured public or private key is invalid."""


class EnvelopeError(BackupCryptoError):
    """Raised when an envelope is invalid, truncated, or unauthentic."""


def key_fingerprint(public_key: PublicKey | bytes) -> str:
    """Return the stable, non-secret identifier for an X25519 public key."""

    raw = bytes(public_key)
    if len(raw) != PublicKey.SIZE:
        raise KeyConfigurationError("invalid public key length")
    return _KEY_ID_PREFIX + hashlib.sha256(raw).hexdigest()


def _decode_base64_key(value: str | bytes, expected_size: int, kind: str) -> bytes:
    if isinstance(value, str):
        encoded = value.strip().encode("ascii", errors="strict")
    elif isinstance(value, bytes):
        encoded = value.strip()
    else:
        raise KeyConfigurationError(f"invalid {kind} key encoding")
    if not encoded:
        raise KeyConfigurationError(f"missing {kind} key")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise KeyConfigurationError(f"invalid {kind} key encoding") from exc
    if len(raw) != expected_size:
        raise KeyConfigurationError(f"invalid {kind} key length")
    return raw


def load_public_key_base64(value: str | bytes) -> PublicKey:
    return PublicKey(_decode_base64_key(value, PublicKey.SIZE, "public"))


def load_private_key_base64(value: str | bytes) -> PrivateKey:
    return PrivateKey(_decode_base64_key(value, PrivateKey.SIZE, "private"))


def encode_key_base64(key: PublicKey | PrivateKey | bytes) -> str:
    return base64.b64encode(bytes(key)).decode("ascii")


def generate_keypair() -> tuple[PrivateKey, PublicKey]:
    private_key = PrivateKey.generate()
    return private_key, private_key.public_key


def _validate_public_metadata(metadata: Mapping[str, object], chunk_size: int) -> dict[str, object]:
    backup_id = metadata.get("backup_id")
    created_at = metadata.get("created_at")
    if not isinstance(backup_id, str):
        raise EnvelopeError("backup_id is required")
    try:
        uuid.UUID(backup_id)
    except (ValueError, AttributeError) as exc:
        raise EnvelopeError("backup_id is invalid") from exc
    if not isinstance(created_at, str) or not created_at:
        raise EnvelopeError("created_at is required")
    if not 1 <= chunk_size <= MAX_CHUNK_SIZE:
        raise EnvelopeError("chunk size is invalid")
    return {
        "format": FORMAT_NAME,
        "version": FORMAT_VERSION,
        "backup_id": backup_id,
        "created_at": created_at,
        "key_id": metadata["key_id"],
        "content_cipher": "secretstream_xchacha20poly1305",
        "key_wrap": "sealed_box_x25519_xsalsa20poly1305",
        "chunk_size": chunk_size,
    }


def _canonical_json(value: Mapping[str, object]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _read_exact(stream: BinaryIO, size: int, label: str) -> bytes:
    data = stream.read(size)
    if len(data) != size:
        raise EnvelopeError(f"truncated {label}")
    return data


def _sha256_stream(stream: BinaryIO) -> str:
    digest = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(chunk)
    return digest.hexdigest()


def _read_prefix(stream: BinaryIO) -> tuple[dict[str, object], bytes, bytes, bytes]:
    magic = _read_exact(stream, len(MAGIC), "envelope magic")
    if magic != MAGIC:
        raise EnvelopeError("not a Mochi backup envelope")
    version = _read_exact(stream, 1, "format version")[0]
    if version != FORMAT_VERSION:
        raise EnvelopeError("unsupported envelope version")
    header_length_bytes = _read_exact(stream, _U32.size, "header length")
    header_length = _U32.unpack(header_length_bytes)[0]
    if not 1 <= header_length <= MAX_HEADER_SIZE:
        raise EnvelopeError("invalid envelope header length")
    header_bytes = _read_exact(stream, header_length, "envelope header")
    try:
        header = json.loads(header_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EnvelopeError("invalid envelope header") from exc
    if not isinstance(header, dict):
        raise EnvelopeError("invalid envelope header")
    required = {
        "format": FORMAT_NAME,
        "version": FORMAT_VERSION,
        "content_cipher": "secretstream_xchacha20poly1305",
        "key_wrap": "sealed_box_x25519_xsalsa20poly1305",
    }
    for key, expected in required.items():
        if header.get(key) != expected:
            raise EnvelopeError("invalid envelope metadata")
    if not isinstance(header.get("backup_id"), str) or not isinstance(header.get("created_at"), str):
        raise EnvelopeError("invalid envelope metadata")
    try:
        uuid.UUID(header["backup_id"])
    except (ValueError, AttributeError) as exc:
        raise EnvelopeError("invalid envelope metadata") from exc
    key_id = header.get("key_id")
    if not isinstance(key_id, str) or not key_id.startswith(_KEY_ID_PREFIX):
        raise EnvelopeError("invalid envelope key identifier")
    chunk_size = header.get("chunk_size")
    if not isinstance(chunk_size, int) or isinstance(chunk_size, bool) or not 1 <= chunk_size <= MAX_CHUNK_SIZE:
        raise EnvelopeError("invalid envelope chunk size")

    sealed_length_bytes = _read_exact(stream, _U16.size, "sealed key length")
    sealed_length = _U16.unpack(sealed_length_bytes)[0]
    expected_sealed_length = bindings.crypto_secretstream_xchacha20poly1305_KEYBYTES + bindings.crypto_box_SEALBYTES
    if sealed_length != expected_sealed_length:
        raise EnvelopeError("invalid sealed key length")
    sealed_key = _read_exact(stream, sealed_length, "sealed key")
    stream_header = _read_exact(
        stream,
        bindings.crypto_secretstream_xchacha20poly1305_HEADERBYTES,
        "secretstream header",
    )
    authenticated_prefix = (
        MAGIC
        + bytes((version,))
        + header_length_bytes
        + header_bytes
        + sealed_length_bytes
        + sealed_key
        + stream_header
    )
    return header, sealed_key, stream_header, authenticated_prefix


def inspect_envelope(path: str | os.PathLike[str]) -> dict[str, object]:
    """Read unauthenticated public metadata and hash the exact opened file."""

    with Path(path).open("rb") as stream:
        header, _, _, _ = _read_prefix(stream)
        stream.seek(0)
        ciphertext_sha256 = _sha256_stream(stream)
    return {
        "format": header["format"],
        "version": header["version"],
        "backup_id": header["backup_id"],
        "created_at": header["created_at"],
        "key_id": header["key_id"],
        "content_cipher": header["content_cipher"],
        "key_wrap": header["key_wrap"],
        "ciphertext_sha256": ciphertext_sha256,
        "metadata_authenticated": False,
        "sender_identity_authenticated": False,
    }


def encrypt_file(
    source: str | os.PathLike[str],
    destination: str | os.PathLike[str],
    public_key: PublicKey,
    *,
    backup_id: str,
    created_at: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> dict[str, object]:
    """Encrypt *source* to an authenticated v1 ``.mbak`` envelope."""

    source_path = Path(source)
    destination_path = Path(destination)
    if destination_path.exists():
        raise FileExistsError(destination_path)
    key_id = key_fingerprint(public_key)
    header = _validate_public_metadata(
        {"backup_id": backup_id, "created_at": created_at, "key_id": key_id},
        chunk_size,
    )
    header_bytes = _canonical_json(header)
    if len(header_bytes) > MAX_HEADER_SIZE:
        raise EnvelopeError("envelope header is too large")

    content_key = bindings.crypto_secretstream_xchacha20poly1305_keygen()
    sealed_key = SealedBox(public_key).encrypt(content_key)
    state = bindings.crypto_secretstream_xchacha20poly1305_state()
    stream_header = bindings.crypto_secretstream_xchacha20poly1305_init_push(state, content_key)
    prefix = (
        MAGIC
        + bytes((FORMAT_VERSION,))
        + _U32.pack(len(header_bytes))
        + header_bytes
        + _U16.pack(len(sealed_key))
        + sealed_key
        + stream_header
    )

    partial_path = destination_path.with_name(destination_path.name + f".{uuid.uuid4().hex}.partial")
    try:
        with source_path.open("rb") as plaintext, partial_path.open("xb") as encrypted:
            os.chmod(partial_path, 0o600)
            encrypted.write(prefix)
            current = plaintext.read(chunk_size)
            if not current:
                frame = bindings.crypto_secretstream_xchacha20poly1305_push(
                    state,
                    b"",
                    ad=prefix,
                    tag=bindings.crypto_secretstream_xchacha20poly1305_TAG_FINAL,
                )
                encrypted.write(_U32.pack(len(frame)))
                encrypted.write(frame)
            else:
                while True:
                    following = plaintext.read(chunk_size)
                    final = not following
                    frame = bindings.crypto_secretstream_xchacha20poly1305_push(
                        state,
                        current,
                        ad=prefix,
                        tag=(
                            bindings.crypto_secretstream_xchacha20poly1305_TAG_FINAL
                            if final
                            else bindings.crypto_secretstream_xchacha20poly1305_TAG_MESSAGE
                        ),
                    )
                    encrypted.write(_U32.pack(len(frame)))
                    encrypted.write(frame)
                    if final:
                        break
                    current = following
            encrypted.flush()
            os.fsync(encrypted.fileno())
        os.replace(partial_path, destination_path)
        os.chmod(destination_path, 0o600)
    except BaseException:
        try:
            partial_path.unlink()
        except FileNotFoundError:
            pass
        raise
    finally:
        # Best-effort removal of the in-memory reference; libsodium handles
        # randomness and authenticated encryption, but Python cannot promise a
        # secure memory wipe for immutable bytes.
        content_key = b""
    return dict(header)


def decrypt_file(
    source: str | os.PathLike[str],
    destination: str | os.PathLike[str],
    private_key: PrivateKey,
    *,
    overwrite: bool = False,
) -> dict[str, object]:
    """Verify secretstream AEAD integrity and decrypt atomically.

    This does not establish sender identity because anyone with the recipient
    public key can construct an envelope.  Callers must verify trusted
    provenance separately (the offline CLI pins the bot-published SHA-256).
    """

    source_path = Path(source)
    destination_path = Path(destination)
    if destination_path.exists() and not overwrite:
        raise FileExistsError(destination_path)
    partial_path = destination_path.with_name(destination_path.name + f".{uuid.uuid4().hex}.partial")
    try:
        with source_path.open("rb") as encrypted:
            header, sealed_key, stream_header, prefix = _read_prefix(encrypted)
            if header["key_id"] != key_fingerprint(private_key.public_key):
                raise EnvelopeError("private key does not match envelope key identifier")
            try:
                content_key = SealedBox(private_key).decrypt(sealed_key)
            except CryptoError as exc:
                raise EnvelopeError("unable to unwrap envelope key") from exc
            state = bindings.crypto_secretstream_xchacha20poly1305_state()
            try:
                bindings.crypto_secretstream_xchacha20poly1305_init_pull(state, stream_header, content_key)
            except (CryptoError, ValueError) as exc:
                raise EnvelopeError("invalid secretstream header") from exc
            final_seen = False
            with partial_path.open("xb") as plaintext:
                os.chmod(partial_path, 0o600)
                while True:
                    frame_length_bytes = encrypted.read(_U32.size)
                    if not frame_length_bytes:
                        break
                    if len(frame_length_bytes) != _U32.size:
                        raise EnvelopeError("truncated frame length")
                    frame_length = _U32.unpack(frame_length_bytes)[0]
                    maximum = int(header["chunk_size"]) + bindings.crypto_secretstream_xchacha20poly1305_ABYTES
                    if not bindings.crypto_secretstream_xchacha20poly1305_ABYTES <= frame_length <= maximum:
                        raise EnvelopeError("invalid encrypted frame length")
                    frame = _read_exact(encrypted, frame_length, "encrypted frame")
                    try:
                        message, tag = bindings.crypto_secretstream_xchacha20poly1305_pull(state, frame, ad=prefix)
                    except CryptoError as exc:
                        raise EnvelopeError("envelope authentication failed") from exc
                    if tag == bindings.crypto_secretstream_xchacha20poly1305_TAG_FINAL:
                        final_seen = True
                        plaintext.write(message)
                        if encrypted.read(1):
                            raise EnvelopeError("data follows final encrypted frame")
                        break
                    if tag != bindings.crypto_secretstream_xchacha20poly1305_TAG_MESSAGE:
                        raise EnvelopeError("unexpected secretstream tag")
                    plaintext.write(message)
                if not final_seen:
                    raise EnvelopeError("missing authenticated final frame")
                plaintext.flush()
                os.fsync(plaintext.fileno())
        if destination_path.exists() and not overwrite:
            raise FileExistsError(destination_path)
        os.replace(partial_path, destination_path)
        os.chmod(destination_path, 0o600)
    except BaseException:
        try:
            partial_path.unlink()
        except FileNotFoundError:
            pass
        raise
    finally:
        content_key = b""
    verified = dict(header)
    verified["aead_frame_integrity_verified"] = True
    verified["sender_identity_authenticated"] = False
    return verified
