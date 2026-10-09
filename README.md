# DRL Watcher — ticket-event notifier bot for ctsv.hust.edu.vn

A small bot that calls the same API the **"Đặt vé" (Book ticket)** page uses
(`/bknexus/Event/GetEvents`), checks it on a short interval, and **pushes a Telegram
message to your phone** as soon as:

- 🎟️ A **new event** appears
- 🔔 An event **switches to "registration open"** (the key moment for grabbing a slot)
- ♻️ A full event **frees up a slot again**

The bot only **notifies** — you tap the link and register yourself. No school password required.

---

## Requirements

- **Python 3** (standard library only — nothing to `pip install`).
- The **Telegram** app on your phone.

---

## One-time setup (~5 minutes)

### Step 1 — Create a Telegram bot
1. Open Telegram, find **@BotFather**, tap **Start**.
2. Send `/newbot`, choose a name and a username (must end in `bot`).
3. BotFather returns a **token** like `123456789:AAE...` → **copy** it.
4. Open your new bot's link and tap **Start** (so it may message you).

### Step 2 — Get `TokenBKNexus` and your student ID from the website
1. In a browser, log in to **https://ctsv.hust.edu.vn** as usual.
2. Press **F12** → **Application** tab (Chrome/Edge) or **Storage** (Firefox).
3. On the left: **Cookies** → select `https://ctsv.hust.edu.vn`.
4. Copy the value of the **`TokenBKNexus`** cookie.
   - Also note the **`UserName`** cookie (your student ID) to match it.

> The token usually lasts a while. When it expires, the bot will message you on Telegram
> asking you to refresh it.

### Step 3 — Fill in `config.json`
1. Copy `config.example.json` to `config.json` (same folder).
2. Edit `config.json`:

```json
{
  "session_token": "<TokenBKNexus cookie value>",
  "username": "<your student ID>",
  "telegram_bot_token": "<token from BotFather>",
  "telegram_chat_id": "",
  "poll_seconds": 30,
  "notify_states": ["OPEN", "SOON"],
  "notify_new_any_state": true
}
```

3. **Get your `telegram_chat_id`:** send the bot any message (e.g. "hi"), then from the
   project folder run:

   ```
   python drl_watch.py getchat
   ```

   It prints a `chat_id` (a number) → paste it into `telegram_chat_id`.

### Step 4 — Verify
```
python drl_watch.py check    # should print the event list -> token OK
python drl_watch.py test     # should deliver a test message on Telegram
```

If both work, you're done.

---

## Running the bot

Simplest: run `python drl_watch.py run` (Windows users can double-click `run.bat`).
While that window stays open, the bot is watching. On first start it sends one
"bot started" message.

### Commands
| Command | What it does |
|---------|--------------|
| `python drl_watch.py run`     | Run the watch loop (default) |
| `python drl_watch.py once`    | Check once and exit (for schedulers / CI) |
| `python drl_watch.py check`   | Print the current event list (token test) |
| `python drl_watch.py getchat` | Get your Telegram `chat_id` |
| `python drl_watch.py test`    | Send a test message |

### Telegram chat commands
Send these to your bot (only your configured `chat_id` is accepted):

| Command | What it does |
|---------|--------------|
| `/status` | Bot health: token validity, number of events tracked, how many are open |
| `/list`   | Events that are **open for registration right now** |
| `/check`  | Force an immediate check |
| `/token <value>` | Update `TokenBKNexus` when it expires |
| `/mssv <id>` | Update the student ID |
| `/help`   | Show the command list |

---

## Configuration

Settings live in `config.json`, or may be supplied via environment variables
(`DRL_SESSION_TOKEN`, `DRL_USERNAME`, `DRL_TELEGRAM_BOT_TOKEN`, `DRL_TELEGRAM_CHAT_ID`),
which take precedence — useful for CI/secrets.

- **Check more/less often:** change `poll_seconds`. Default `30`. Don't go below ~10.
- **Fewer "new but not-yet-open" alerts:** set `notify_new_any_state` to `false` to only
  notify about new events already in `OPEN`/`SOON`.

## Running it 24/7 (no laptop required)

Two documented options:

- **GitHub Actions** (free, no card, checks every ~5 min) — see `GITHUB_ACTIONS.md`.
- **A free always-on cloud VM** (30-second checks, true 24/7) — see `DEPLOY_CLOUD.md`.

## Files
- `drl_watch.py` — the bot.
- `config.json` — your config (contains your token; **never commit or share it**). Ignored by git.
- `config.example.json` — template.
- `state.json` — auto-created; remembers seen events (delete it to "forget" and re-baseline).
- `run.bat` — convenience launcher for Windows.
- `.github/workflows/watch.yml` — the GitHub Actions schedule.
- `deploy/setup.sh` — installs the bot as a systemd service on a Linux VM.

## When the token expires
The bot sends a Telegram message: "⚠️ Token expired". Redo **Step 2** (copy a fresh
`TokenBKNexus`), update `session_token` (or the `DRL_SESSION_TOKEN` secret if running on
GitHub Actions), and the bot resumes.

## Security notes
- `config.json` holds your session token and bot token — keep it private (it is git-ignored).
- When running on GitHub Actions, keep the repository's secrets in **Settings → Secrets**,
  never in the code.
