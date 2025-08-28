# F1 Appeals Bot

A Telegram bot for handling community moderation appeals in F1 discussion groups. Works alongside [tg-spam](https://github.com/umputun/tg-spam) to provide a fair appeals process for users who believe they were incorrectly banned.

## Features

- 🤖 **User Appeals**: Users can submit appeals via DM to the bot
- 🛡️ **Admin Review**: Admins can approve/reject appeals with reasons
- 📊 **Statistics**: Track appeals by status and generate reports
- 🔄 **Smart Unbanning**: Integrates with tg-spam API or fallback to direct Telegram API
- 💾 **Persistent Storage**: SQLite database for reliable data storage
- 🌐 **Multi-language**: Supports Russian and English F1 community discussions

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User banned   │───▶│ Appeals Bot DM  │───▶│  Admin Group    │
│   from F1 group │    │   /appeal ...   │    │ /approve /reject│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   SQLite DB     │    │   tg-spam API   │
                       │  (Appeals Log)  │    │   (Unban User)  │
                       └─────────────────┘    └─────────────────┘
```

## Quick Start

### 1. Create Appeals Bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Use `/newbot` and follow instructions
3. Save the token for `APPEALS_BOT_TOKEN`

### 2. Setup Environment

```bash
cp .env.example .env
# Edit .env with your tokens and group IDs
```

### 3. Run with Docker

```bash
docker-compose up -d
```

### 4. Development Setup

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run bot locally
python -m appeals_bot.main
```

## Configuration

| Environment Variable | Description | Required | Default |
|---------------------|-------------|----------|---------|
| `APPEALS_BOT_TOKEN` | Appeals bot token from BotFather | ✅ | - |
| `MAIN_GROUP_ID` | F1 group ID (negative number) | ✅ | - |
| `ADMIN_GROUP_ID` | Admin group ID for notifications | ✅ | - |
| `SPAM_BOT_ADMIN_TOKEN` | Main bot token (for unbanning) | ✅ | - |
| `DATABASE_PATH` | SQLite database file path | ❌ | `/data/appeals.db` |
| `LOG_LEVEL` | Logging level | ❌ | `INFO` |
| `USE_TG_SPAM_API` | Use tg-spam API for unbanning | ❌ | `true` |

## User Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Show welcome message and instructions | `/start` |
| `/appeal [text]` | Submit an appeal with explanation | `/appeal I was discussing race strategy, not attacking anyone` |
| `/status` | Check your appeals status | `/status` |
| `/help` | Show help message | `/help` |

## Admin Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/approve [id]` | Approve appeal and unban user | `/approve 123` |
| `/reject [id] [reason]` | Reject appeal with reason | `/reject 123 Still violated community rules` |
| `/info [id]` | Get detailed appeal information | `/info 123` |
| `/pending` | List all pending appeals | `/pending` |
| `/stats` | Show appeals statistics | `/stats` |

## Appeals Workflow

1. **User gets banned** by tg-spam moderation
2. **User contacts appeals bot** via DM: `/appeal [explanation]`
3. **Admin gets notification** in admin group with user details
4. **Admin reviews appeal**:
   - `/approve 123` - Unbans user and notifies them
   - `/reject 123 [reason]` - Rejects with explanation
5. **User gets notified** of the decision automatically
6.
