# Discord Utility Bot

A lightweight Discord bot built with [`discord.py`](https://discordpy.readthedocs.io/) that provides quick utilities, role management, and fun extras. Uses `dotenv` for secure token loading and writes debug logs to `discord.log`.

---

## ✨ Features

* **General**: latency check, greetings, server/bot info in a rich embed
* **Role management** (requires proper permissions): create, delete, and assign roles to mentioned users
* **Fun**: random "brick" emoji spammer (uses your custom emojis)
* **Structured logging**: file-based logging at `DEBUG` level

---

## 🧱 Commands

> Default prefix: **`b`** (or mention the bot). Examples below assume the prefix.

### General

| Command  | Usage       | Description                                                               |
| -------- | ----------- | ------------------------------------------------------------------------- |
| `bping`  | `bping`     | Replies with bot latency in ms.                                           |
| `bhello` | `bhello`    | Greets the author by name.                                                |
| `binfo`  | `binfo`     | Shows bot/server info in an embed.                                        |
| `brick`  | `brick [n]` | Sends *n* random custom “brick” emojis (1–10). If out of range, sends 10. |

### Roles (requires **Moderator** in your roles **and** the bot’s role to have required perms)

| Command  | Usage                                  | Description                                                                           |
| -------- | -------------------------------------- | ------------------------------------------------------------------------------------- |
| `bcrole` | `bcrole <role_name> [#HEX]`            | Creates a role with an optional hex color (e.g., `#FF0000`). Random color if omitted. |
| `brrole` | `brrole <role_name>`                   | Deletes a role by name.                                                               |
| `barole` | `barole <role_name> @user1 @user2 ...` | Adds an existing role to all mentioned members.                                       |

> The help menu is available via `bhelp` (custom embed).

---

## 🔐 Permissions & Intents

This bot uses privileged intents and role-management APIs. Make sure ALL of these are configured:

### In the **Discord Developer Portal** → *Your App* → **Bot**

* **Privileged Gateway Intents**: ✅ *MESSAGE CONTENT*, ✅ *SERVER MEMBERS*
* (Optional if you plan moderation features) ✅ *GUILD MODERATION*

### On your **server** (for the bot role)

* **Manage Roles** (to create/delete roles and assign them)
* **Read Messages/View Channels**, **Send Messages**, **Embed Links**

> **Role hierarchy rule**: the bot’s highest role must be **above** any role it needs to create or assign.

---

## 🧰 Requirements

* Python **3.10+**
* `discord.py` **2.x**
* `python-dotenv`

Install deps:

```bash
pip install -U discord.py python-dotenv
```

---

## 🔧 Setup & Run

1. **Create a bot** at the [Discord Developer Portal](https://discord.com/developers/applications), add a **Bot** user, and copy the **Token**.
2. **Enable intents** as listed above.
3. **Invite the bot** to your server using an OAuth2 URL with scopes `bot` (and optionally `applications.commands`) and permissions including `Manage Roles`, `Send Messages`, `Embed Links`.
4. **Project files**: put your Python file (e.g., `bot.py`) alongside a `.env` file:

```
.env
bot.py
```

5. **Create `.env`** with your token:

```
DISCORD_TOKEN=YOUR_BOT_TOKEN_HERE
```

6. **Run** the bot:

```bash
python bot.py
```

> Logs will be written to `discord.log` (rotated on each run due to `mode='w'`).

---

## 🧩 Notes about Emojis (Brick command)

The `brick` command references custom emojis by ID (e.g., `<:ting:1433593486883684393>`). These **must exist in a server the bot can see**. Replace them with emojis available to your server or standard Unicode emojis.

---

## 🧪 Local Dev Tips

* Use a **.gitignore** to avoid committing your `.env` and `discord.log`:

```
.env
discord.log
__pycache__/
```

* Consider creating a **test server** for development.
* If you refactor command names, update the help embed table above to match.

---

## 🩺 Troubleshooting

* **`Privileged intent is not enabled`**: Enable *Message Content* and *Server Members* in the Developer Portal (Bot tab) and restart.
* **`Missing Permissions` on role ops**: Grant the bot **Manage Roles**, and move the bot’s highest role **above** the target role in the role list.
* **Mentions not working in `barole`**: Ensure you actually mention members (`@User`). The command reads `ctx.message.mentions`.
* **Color parse error**: Provide a valid hex like `#00FF99`.

---

## 📁 Project Structure (suggested)

```
.
├── bot.py           # your main script (code sample below)
├── .env             # DISCORD_TOKEN=...
├── requirements.txt # optional pinning
└── README.md
```

**requirements.txt** (optional)

```
discord.py>=2.3.0
python-dotenv>=1.0.0
```

---

## 🛡️ Security

* **Never** hardcode tokens; keep them in `.env`.
* Rotate your token if it leaks (`Developer Portal` → Regenerate).
* Limit the bot’s permissions scope to what you actually need.

---

## 📜 License

MIT (or choose your preferred license).

---

## 🧩 Code Reference

Below is the command set this README targets (trimmed for clarity):

```py
# Prefix: b, and mention handling via commands.when_mentioned_or('b')
# Commands: ping, hello, xdd, crole, rrole, arole, info, rick/brick, help
# Intents: message_content=True, members=True
# Logging: discord.log at DEBUG
```

> Reminder: if you later rename commands (`rick` → `brick`), reflect the change both in code and in the tables above.
