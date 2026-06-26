# AGENTS.md — Mochi Bot (Discord Manager Bot)

This file contains system architecture, deployment commands, coding guidelines, and integration rules for AI coding assistants and developers working on the **Mochi Bot** (formerly "General เบ๊") repository.

---

## 🌸 Project Overview
**Mochi Bot** is a multi-purpose Discord bot designed for server management, academic scheduling (KMUTNB curriculum integration), and Discord server utilities. It is fully integrated with a containerized tech stack comprising:
1. **Discord Bot (`main_bot/`)**: Built on `discord.py` and MongoDB.
2. **REST API (`api/`)**: A Flask-based API for stats extraction and bot configuration management.
3. **Web Dashboard (`dashboard/`)**: A Next.js (TypeScript) interface for managing command statistics and real-time visualization.

---

## 🛠️ Tech Stack & Key Parameters
- **Language**: Python 3.10+ (Bot & API), TypeScript (Dashboard)
- **Discord Library**: `discord.py` 2.x (using Application Commands / hybrid commands)
- **Database**: MongoDB (async queries using `Motor` driver via `AsyncIOMotorClient`)
- **Web App**: Next.js (App Router) + Tailwind CSS
- **Prefixes**: Case-insensitive prefix support — handles `b`, `B`, `t`, `T`, and Bot Mentions.
- **Default Bot Presence**: "In Sakura Garden 🌸"

---

## 📂 Project Structure & Key Paths
```
discord-manager-bot/
├── main_bot/                 # Core Discord Bot
│   ├── main.py               # Bot entrypoint, BotInitDB class
│   ├── cogs/                 # Modular extension blocks
│   │   ├── system/
│   │   │   └── heartbeat.py  # Heartbeat monitor & status toggle
│   │   ├── academic/
│   │   │   └── schedule.py   # Class curriculum & schedule commands
│   │   ├── configuration/    # Role, Channel & Maintenance cogs
│   │   ├── utility/          # Info, randomizers, and helpers
│   │   └── backup/
│   ├── validation/           # User, role, and channel privilege checks
│   ├── components/           # Paginator and scheduled views (React-like Selects/Buttons)
│   ├── requirements.txt      # Bot dependencies
│   └── Dockerfile
├── api/                      # Flask API service (re-routing configs to bot)
├── dashboard/                # Next.js Web Dashboard
├── docker-compose.yml        # Multi-container dev orchestrator
└── docker-compose.prod.yml   # Production compose runner
```

---

## 💓 Hermes Heartbeat & Liveness System
Mochi Bot is equipped with a health-check monitor (`main_bot/cogs/system/heartbeat.py`) that observes liveness pings from Hermes Agent:
1. **Liveness Channel**: Designated thread ID `1514163672857972757` (stored as `HEARTBEAT_CHANNEL_ID` in `.env`).
2. **Cron Job Ping**: Hermes cron job `d735f0aa313e` sends a heartbeat ping (emoji `💓`) to the thread every 2 minutes.
   - *Note*: Hermes pings require the header `"User-Agent: DiscordBot/1.0"` to bypass Discord API 403 blocks.
3. **Liveness State Engine**:
   - The monitor runs every 2 minutes.
   - If no heartbeat ping is received within the timeout window (`HEARTBEAT_TIMEOUT`, default 360 seconds), Mochi Bot switches status to **Idle** with presence: `"Mochi is sleeping~ 💤"`.
   - Once a heartbeat ping is received again, status automatically restores to **Online** with presence: `"In Sakura Garden 🌸"`.

---

## 🧹 Historical Refactors (CRITICAL)
- **Homework Feature REMOVED**: The homework manager has been entirely deprecated.
  - `cogs/academic/homework_manager.py` has been **deleted**.
  - All homework-related command references have been cleaned from `info.py` and `main.py`.
  - **Do NOT re-introduce any homework manager features** or commands unless specifically requested by Conde.

---

## 💻 Common Commands

### Local Running
```bash
# Run the Bot locally
cd main_bot
pip install -r requirements.txt
python main.py

# Run API
cd api
python app.py
```

### Docker Deployment (Railway/Local)
```bash
# Production deployment with background containers
docker-compose -f docker-compose.prod.yml up -d --build
```
*Note: Production CI/CD is wired up with GitHub Actions pointing towards Railway deployment platforms.*

---

## 📝 Coding Guidelines & Standards

### Bot Cogs (`discord.ext.commands`)
1. **Use Hybrid Commands**: Define commands using `@commands.hybrid_command()` to automatically register both traditional text-prefix commands (`bcmd`) and Slash Commands (`/cmd`).
2. **Async Operations**: All external queries and API calls must be async. Use Motor's async query syntax (e.g. `await self.db.collection.find_one(...)`).
3. **Validation Guards**: Restrict restricted commands with validation decorators (e.g., `@validation.role()` or `@validation.channel()`).

### Discord Gateway Compatibility
- Ensure `intents.message_content = True` and `intents.members = True` are initialized in `main.py` since the bot listens to thread content and handles member tracking.
