# Mochi Bot

Mochi Bot is a Discord server-management and academic utility bot with a Flask API and a Next.js dashboard. The repository contains three services:

- `main_bot/`: `discord.py` bot and its internal status API
- `api/`: dashboard API, Discord OAuth, and MongoDB-backed configuration
- `dashboard/`: Next.js control panel

The current command and permission inventory is in [docs/FEATURE_AUDIT.md](docs/FEATURE_AUDIT.md). The removed homework feature must not be reintroduced; any legacy collection is preserved until a separate retention decision is made.

## Setup

Requirements are Python 3.10+, Node.js 20+, MongoDB, and a Discord application. Docker is optional but is the simplest way to run the complete stack.

1. Create local configuration:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Fill the blank values in `.env`. At minimum, the bot needs `DISCORD_TOKEN`, `MONGO_URI`, `MONGO_DB`, and `GUILD_ID`. OAuth additionally needs `DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET`, `OAUTH_REDIRECT_URI`, and a strong, unique `JWT_SECRET`.

   The API fails to start when `JWT_SECRET` is missing or blank. Changing it invalidates existing dashboard sessions.

3. Start the development stack:

   ```powershell
   docker compose up --build
   ```

Development Compose forces `INSTANCE=dev` and `BACKUP_ENABLED=false`. It exposes the bot on port 8080, the API on 5000, and the dashboard on 3000.

For direct service development, install each service's dependencies from its own directory. `python-dotenv` reads the working directory's `.env`, so create an ignored service-local `.env` when running `python main.py` or `python app.py` outside Compose. Do not commit it.

```powershell
cd main_bot
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

```powershell
cd api
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

```powershell
cd dashboard
npm ci
npm run dev
```

Production Compose uses the published images, forces `INSTANCE=server`, and leaves scheduled backups disabled unless `BACKUP_ENABLED=true` is explicitly configured:

```powershell
docker compose -f docker-compose.prod.yml up -d
```

Before enabling scheduled backups in production, complete and test the encrypted-backup rollout below. The production file defaults `BACKUP_ENABLED` to `false`, so the bot can be deployed safely while manual recovery testing is completed.

## Database-name migration

`MONGO_DB` is the canonical database-name setting used by the bot and API. `MAIN_DB` is deprecated.

1. Set `MONGO_DB` to the exact database name previously supplied through `MAIN_DB`.
2. Start the bot with backups disabled and verify commands and dashboard reads against the expected data.
3. Remove `MAIN_DB` from the deployment after every service has moved to `MONGO_DB`.

This migration changes configuration only. It must not rename, copy, or delete MongoDB collections.

## Encrypted backups

Backups are encrypted before they leave the bot. The offline tool generates base64-encoded X25519 keys. The running bot receives only the single-line public-key value through `BACKUP_ENCRYPTION_PUBLIC_KEY`; the matching private-key file stays offline with the operator. Never put the private key in `.env`, the container image, the deployment platform, Discord, or the repository. Recipient public-key encryption provides confidentiality and AEAD frame integrity, but it does not identify the sender: anyone with the public key can create an envelope. Recovery therefore also requires the ciphertext SHA-256 from the trusted bot-authored Discord message.

Run the offline CLI from the repository root. It refuses to overwrite existing outputs and does not print key material:

```powershell
# Keep every key and recovery artifact outside the repository checkout.
$RecoveryDir = Join-Path $HOME "mochi-backup-recovery"
New-Item -ItemType Directory -Force $RecoveryDir | Out-Null
$PrivateKey = Join-Path $RecoveryDir "mochi-backup.key"
$PublicKey = Join-Path $RecoveryDir "mochi-backup.pub"
$Envelope = Join-Path $RecoveryDir "downloaded-backup.mbak"
$OutputZip = Join-Path $RecoveryDir "recovered-backup.zip"

# Generate the recovery keypair on an offline machine.
python -m main_bot.tools.backup_crypto generate --private-key $PrivateKey --public-key $PublicKey

# Read unauthenticated public metadata and the downloaded file's SHA-256.
python -m main_bot.tools.backup_crypto inspect $Envelope

# Copy this exact digest from the trusted bot-authored Discord message, not from the file.
$ExpectedSha256 = "<trusted-Discord-ciphertext-SHA-256>"

# Pin provenance to that digest, verify AEAD frame integrity, and recover a new ZIP.
python -m main_bot.tools.backup_crypto decrypt $Envelope --private-key $PrivateKey --expected-sha256 $ExpectedSha256 --output $OutputZip
```

Deploy the contents of `$PublicKey` as `BACKUP_ENCRYPTION_PUBLIC_KEY`, set `BACKUP_CHANNEL_ID`, and keep `MONGO_DB` canonical. The backup artifact uses the `.mbak` extension. There is no plaintext fallback: a missing/invalid key, failed export, failed encryption, or failed delivery must produce a failed backup rather than an unencrypted upload. Temporary plaintext exports and the protected `mongoexport` URI config must be cleaned up on both success and failure.

Use this staged rollout:

1. Keep `BACKUP_ENABLED=false`.
2. Configure the public key and destination channel, then have the Discord bot owner trigger one manual `backup` command.
3. Download the resulting `.mbak` and separately copy its SHA-256 from the trusted bot-authored Discord message. Inspect the file's explicitly unauthenticated public metadata, then pass the trusted digest with `--expected-sha256` when decrypting. Open the digest-pinned, AEAD-integrity-verified output ZIP and verify expected collections and representative records.
4. Delete the decrypted ZIP and any extracted test output securely when verification is complete.
5. Set `BACKUP_ENABLED=true` only after the complete recovery test passes.

Retain the private key and recovery procedure according to your incident-recovery policy. Losing the private key makes encrypted backups unrecoverable.

## Validation

Useful local checks are:

```powershell
docker compose config
docker compose -f docker-compose.prod.yml config

cd dashboard
npm run lint
npm run build
```

Compose reads `.env`; use placeholders in a disposable file for configuration-only validation and never print a populated secret file to logs.
