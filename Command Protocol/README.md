# COMMAND PROTOCOL — Discord Bot

```
╔══════════════════════════════════════════════════════╗
║       COMMAND PROTOCOL // COMMAND TERMINAL BOT       ║
║           Official Community Discord Bot             ║
╚══════════════════════════════════════════════════════╝
```

A fully-featured Discord bot for the **Command Protocol** RTS game community server.
Built with `discord.py` using slash commands, Discord embeds, and JSON file storage.

---

## 📁 Project Structure

```
command_protocol_bot/
├── bot.py                    # Main entry point
├── config.json               # Bot token & server configuration
├── requirements.txt          # Python dependencies
│
├── cogs/                     # Feature modules (one cog per feature area)
│   ├── faction.py            # /join, /army, /rebels, /switchside
│   ├── information.py        # /about, /roadmap, /progress, /status, /devlog, /changelog
│   ├── community.py          # /suggest, /bugreport
│   └── admin.py              # /updatedevlog, /updatechangelog, /updateprogress, /announce
│
├── utils/                    # Shared utilities
│   ├── config.py             # Config loader
│   ├── data_manager.py       # JSON read/write layer
│   ├── embeds.py             # Embed factory & brand styles
│   └── checks.py             # Permission helpers
│
└── data/                     # Auto-created JSON storage
    ├── game_info.json
    ├── devlog.json
    ├── changelog.json
    ├── progress.json
    ├── roadmap.json
    ├── suggestions.json
    └── bug_reports.json
```

---

## ⚡ Quick Start

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Create Your Discord Bot
1. Go to [discord.com/developers](https://discord.com/developers/applications)
2. Create a **New Application** → name it "Command Protocol"
3. Go to **Bot** tab → click **Add Bot**
4. Under **Privileged Gateway Intents**, enable:
   - **Server Members Intent**
   - **Message Content Intent**
5. Copy your **Bot Token**

### 3. Configure the Bot
Edit `config.json`:

```json
{
    "BOT_TOKEN": "your-real-token-here",
    "GUILD_ID": "your-server-id",
    "ADMIN_ROLE_IDS": ["role-id-1", "role-id-2"],
    "ARMY_ROLE_ID": "army-role-id",
    "REBELS_ROLE_ID": "rebels-role-id",
    "SUGGESTION_CHANNEL_ID": "channel-id",
    "BUGREPORT_CHANNEL_ID": "channel-id",
    "ANNOUNCE_CHANNEL_ID": "channel-id"
}
```

> **To get IDs**: Enable Developer Mode in Discord Settings → right-click any server, channel, or role → Copy ID

### 4. Invite the Bot to Your Server
Generate an invite URL with these permissions:
- `Manage Roles`
- `Send Messages`
- `Embed Links`
- `Use Slash Commands`

Or use this URL pattern (replace `CLIENT_ID`):
```
https://discord.com/api/oauth2/authorize?client_id=CLIENT_ID&permissions=268437504&scope=bot%20applications.commands
```

### 5. Run the Bot
```bash
python bot.py
```

---

## 🔧 Creating Discord Roles

Before using faction commands, create these roles in your server:
- **The Army** (suggested color: `#2E86AB` — steel blue)
- **The Rebel Movement** (suggested color: `#E63946` — crimson)

Then add their IDs to `config.json`.

---

## 📋 Command Reference

### Faction Commands
| Command | Description |
|---------|-------------|
| `/join army` | Enlist in The Army |
| `/join rebels` | Join the Rebel Movement |
| `/army` | View Army faction lore & info |
| `/rebels` | View Rebel Movement lore & info |
| `/switchside` | Defect to the opposite faction |

### Information Commands
| Command | Description |
|---------|-------------|
| `/about` | Game overview and description |
| `/roadmap` | Development phase roadmap |
| `/progress` | Detailed completion status |
| `/status` | Quick status dashboard |
| `/devlog` | Latest developer log |
| `/changelog` | Latest update notes |

### Community Commands
| Command | Description |
|---------|-------------|
| `/suggest` | Submit a suggestion (opens modal form) |
| `/bugreport` | Submit a bug report (opens modal form) |

### Admin Commands *(requires Admin role or Discord Administrator)*
| Command | Description |
|---------|-------------|
| `/updatedevlog` | Update the dev log entry |
| `/updatechangelog` | Update the changelog |
| `/updateprogress` | Update progress data |
| `/announce` | Post an official announcement |

---

## 🛠 Customizing Data

All game content is stored in `data/*.json`. You can:
- Edit `data/game_info.json` to update game description, version, and links
- Edit `data/roadmap.json` to update phases and items
- Edit `data/progress.json` to update completion percentages and system lists
- Use the `/update*` admin commands in Discord for live updates

---

## 📝 Development Notes

- **Slash command sync**: The first time you run the bot, commands may take up to 1 hour to appear globally. Set a `GUILD_ID` in config for instant sync to your dev server.
- **Role permissions**: The bot's role must be positioned *above* The Army and Rebel roles in your server's role hierarchy for it to assign/remove them.
- **Expanding the bot**: Add new cogs in `cogs/`, register them in `bot.py`'s `setup_hook`, and they'll load automatically.

---

## 🎨 Embed Color Reference

| Color | Hex | Usage |
|-------|-----|-------|
| Electric Blue | `#00B4FF` | Default / Info |
| Steel Blue | `#2E86AB` | Army faction |
| Crimson | `#E63946` | Rebel faction |
| Matrix Green | `#00FF87` | Success / Confirm |
| Amber | `#FFBE0B` | Warning |
| Red Alert | `#FF3860` | Error |
| Slate | `#8B9BB4` | Neutral / Lore |
| Purple | `#AA00FF` | Admin actions |
