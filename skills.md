# Project Context: Discord Manager Bot

## Overview
This project is a multi-purpose Discord bot for server management, academic scheduling, and utility. It features a 3-tier architecture with a Python Discord Bot, a Flask REST API backend, and a Next.js web dashboard frontend.

## Architecture & Services
The application is split into three main components, and is fully containerized using Docker Compose:

1. **Bot (`/main_bot`)**: 
   - **Language/Framework**: Python 3.10+, `discord.py`
   - **Database Access**: Uses `motor` (AsyncIOMotorClient) for asynchronous MongoDB interactions.
   - **Structure**: 
     - Organized using `commands.Cog`. Cogs are loaded dynamically from the `cogs/` directory.
     - Discord UI components (Views, Modals, Paginations) are located in `components/`.
     - Validations and checks (e.g., role checks, channel checks) are done via custom decorators in the `validation/` directory.
   - **Entry Point**: `main.py` initializes the bot (`BotInitDB`) and loads extensions.

2. **API (`/api`)**:
   - **Language/Framework**: Python, Flask, Flask-CORS.
   - **Database Access**: Uses `pymongo` (MongoClient) for synchronous MongoDB interactions.
   - **Structure**:
     - Uses Flask Blueprints located in `routes/` (e.g., `auth`, `stats`, `commands`, `channel`).
   - **Entry Point**: `app.py` creates the app and serves it via `waitress`.

3. **Dashboard (`/dashboard`)**:
   - **Language/Framework**: TypeScript, React, Next.js (App Router `src/app`).
   - **Structure**:
     - Modern frontend incorporating responsive glassmorphism designs.
     - Components reside in `src/components/`, state in `src/context/`, and utilities/API interfaces in `src/lib/`.
     - Data models should strictly comply with the API definitions to maintain type safety.

## Shared Resources
- **Database**: Both the bot and the API share a MongoDB database (`discord_bot_db`). Be careful to ensure data schema consistency between the `motor` (async) operations in the bot and `pymongo` (sync) operations in the API.
- **Environment Variables**: The project requires extensive configuration via `.env` (Discord tokens, Mongo URI, OAuth credentials, frontend URL, instance types).

## Agent Guidelines for Modifying This Codebase
- **Adding Bot Commands**: Create or update files inside `main_bot/cogs/`. Prefer `commands.hybrid_command` where applicable to support both prefix and slash commands. Ensure you use the existing validation wrappers from `validation/` (like `@validation.role()` or channel checks).
- **Adding API Endpoints**: Use the blueprint structure in `api/routes/` and register new blueprints in `api/app.py`.
- **Frontend Changes**: Adhere to the existing UI design system. Always check `src/lib/` for shared interfaces before building new data fetching hooks.
- **Docker**: If you add new top-level dependencies, ensure you update `requirements.txt` in the respective Python directories, `package.json` in the dashboard, and consider how it impacts `docker-compose.yml`.
