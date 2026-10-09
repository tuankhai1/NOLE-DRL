# Deploy the bot to a free cloud server (runs 24/7, no laptop needed)

Goal: the bot lives on an always-on server. You can shut your laptop and walk away — it
keeps watching and pushes Telegram alerts to your phone. **Initial setup is done on a
laptop (~20–30 minutes, once).** After that you manage everything from your phone via
Telegram commands.

This guide uses **Oracle Cloud Always Free** (genuinely free forever, the most generous
free tier). But **any Ubuntu server works identically** — if you already have a VPS, skip
to [Part B](#part-b--install-the-bot).

---

## Part A — Create a free server (Oracle Cloud)

> Oracle requires a card (Visa/Mastercard, virtual cards included) **for identity
> verification only** — the Always Free tier is **not charged**. No card? Use GitHub
> Actions instead (`GITHUB_ACTIONS.md`).

1. Go to https://www.oracle.com/cloud/free/ → **Start for free**, sign up (email, country,
   phone + card verification).
2. In the **Oracle Cloud Console**: menu ☰ → **Compute** → **Instances** →
   **Create instance**.
3. Set:
   - **Image**: Canonical **Ubuntu 22.04** (or 24.04).
   - **Shape**: click **Change shape** → **Ampere (ARM)** `VM.Standard.A1.Flex`
     (1 OCPU, 6 GB is plenty) — this is the Always Free part. If ARM is out of capacity,
     pick **VM.Standard.E2.1.Micro** (AMD, also Always Free).
   - **Add SSH keys**: choose **Generate a key pair for me** → click **Save private key**
     (download the `.key` file — keep it safe, you log in with it).
4. **Create**. Wait ~1 minute until the status is **RUNNING**. Note the **Public IP address**.
5. No inbound ports needed — the bot only makes outbound calls. Skip firewall changes.

---

## Part B — Install the bot

Do this on your **laptop**, in the project folder. Open **PowerShell**.

### 1. Test the SSH connection
Replace `<KEY>` = path to the private key you downloaded, `<IP>` = the Public IP:
```powershell
ssh -i "<KEY>" ubuntu@<IP>
```
Type `yes` the first time. If you get a prompt like `ubuntu@...`, it works. Type `exit` to leave.

> Oracle Ubuntu logs in as the **`ubuntu`** user. (Other VPSes may use `root` or another name.)

### 2. Copy the bot + config to the server
Run from the project folder (cd into it first):
```powershell
scp -i "<KEY>" drl_watch.py config.json deploy/setup.sh ubuntu@<IP>:~
```
This uploads 3 files (including your `config.json` with the token already filled in).

### 3. Install (creates a background service)
```powershell
ssh -i "<KEY>" ubuntu@<IP> "bash ~/setup.sh"
```
The script installs `drl_watch.py` into `~/drl`, creates a systemd service `drl-watch`,
starts it immediately, and **restarts it on reboot / on crash**. The last line should show
`Active: active (running)`.

Within seconds your Telegram receives **"🤖 DRL bot started"**. Done! 🎉 You can now close
the laptop — the bot runs independently in the cloud.

---

## Managing from your phone (no laptop needed)

Message your Telegram bot directly:

| Command | What it does |
|---------|--------------|
| `/status` | Is the bot alive, is the token valid, how many events are tracked |
| `/list` | Events **open for registration** right now |
| `/check` | Force an immediate check |
| `/token <value>` | Update the school token (when it expires) |
| `/mssv <id>` | Change the student ID |
| `/help` | Show the command list |

### When the bot says "⚠️ Token expired" — getting a new token from your phone

The school token (`TokenBKNexus`) is a readable browser cookie. On your phone:

**Easy way (bookmarklet — set up once):**
1. Create any bookmark in your phone browser, then **edit its address** to exactly this
   (paste verbatim):
   ```
   javascript:(function(){var m=document.cookie.match(/TokenBKNexus=([^;]+)/);if(!m){alert('Not logged in to ctsv');return;}prompt('Copy the line below and send it to the bot:','/token '+m[1]);})();
   ```
2. When you need a new token: open **https://ctsv.hust.edu.vn** on your phone, **log in**,
   then open that bookmark. It shows a ready `/token xxxxx` line → copy it.
3. Paste that line to your bot. It replies "✅ Token updated".

> Safari (iPhone): bookmark → Edit → paste into the address field. Chrome (Android): save a
> bookmark, then edit its URL. If the browser blocks `javascript:`, use the manual way below.

**Manual way (when you have a laptop):** redo Step 2 in `README.md` (F12 → Cookies → copy
`TokenBKNexus`), then send `/token <value>` to the bot. The token usually lasts a while, so
this is rare.

---

## Server maintenance (over SSH, when needed)

```bash
systemctl status drl-watch        # status
journalctl -u drl-watch -f        # live logs (Ctrl+C to exit)
sudo systemctl restart drl-watch  # restart
sudo systemctl disable --now drl-watch   # stop for good
```

Update the bot (if the code changes later): copy the new `drl_watch.py` up, then:
```bash
cp ~/drl_watch.py ~/drl/drl_watch.py && sudo systemctl restart drl-watch
```

---

## Security notes
- `config.json` on the server holds your `TokenBKNexus` + Telegram token. The server is
  yours, so that's fine — just don't share SSH access or that file.
- Keep the private key (`.key`) safe. Lose it and you lose access to the server (you'd have
  to recreate it).
