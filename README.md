# 🤖 Discord Manager Bot

A multi-purpose Discord bot for server management, academic scheduling, and utility — featuring a modern web dashboard and REST API.

## ✨ Features

- **Server Management** — Role creation, assignment, and channel permissions
- **Academic Tools** — Class schedules and exam tracking with student ID integration
- **Web Dashboard** — Real-time analytics and command usage monitoring (Next.js)
- **REST API** — Statistics and bot control endpoints (Flask)
- **Docker Ready** — Containerized deployment with Docker Compose

## 🛠️ Tech Stack

- **Bot**: Python 3.10+, discord.py, Motor (MongoDB)
- **API**: Flask
- **Dashboard**: Next.js, TypeScripts
- **Database**: MongoDB
- **Deployment**: Docker, Docker Compose

## ⚙️ Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure `.env` with your tokens and MongoDB URI

3. Run the bot:
   ```bash
   python main.py
   ```

## 🐳 Docker Deployment

```bash
docker-compose up -d --build
```

This starts the bot, API (port 5000), and dashboard (port 3000).

---
