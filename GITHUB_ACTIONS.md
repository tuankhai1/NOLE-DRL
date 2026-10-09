# Run the bot on GitHub Actions (free, no card, no laptop)

The bot runs on GitHub's infrastructure, **checking every ~5 minutes** (the smallest
interval GitHub allows; occasionally delayed a few more minutes). The token and sensitive
values live in **Secrets** — **never in the source code**.

> ⚠️ Keep the repo **Public** so GitHub Actions minutes are **free and unlimited**. A
> Private repo is capped at 2000 minutes/month — not enough for a 5-minute schedule. The
> source contains no secrets (those are in Secrets), so Public is safe.

---

## Step 1 — Have a GitHub account
If you don't, sign up at https://github.com (free, email only).

## Step 2 — Create an empty repo
1. https://github.com/new
2. **Repository name**: `drl-watch` (or any name)
3. Choose **Public**.
4. Do **NOT** tick "Add a README" (leave it completely empty).
5. **Create repository**. Note the URL like `https://github.com/<you>/drl-watch.git`.

## Step 3 — Push the code

### Option A — Using Git (recommended)
Open **PowerShell** in the project folder and run (replace `<URL>` with the repo URL):
```powershell
git remote add origin <URL>
git push -u origin main
```
The first push opens a GitHub login in your browser — sign in and you're done.
(The setup already excludes `config.json` from being pushed — only code + workflow go up.)

### Option B — No Git, via the web
1. In the new repo → **Add file → Upload files** → drag **`drl_watch.py`** in → **Commit**.
2. **Add file → Create new file** → type the name `.github/workflows/watch.yml` → paste the
   contents of the project's `.github/workflows/watch.yml` → **Commit**.
3. **Never** upload `config.json`.

## Step 4 — Add Secrets
In the repo: **Settings → Secrets and variables → Actions → New repository secret**. Create
**4 secrets** (names spelled exactly), with values copied from your `config.json`:

| Secret name | Value (from config.json) |
|-------------|--------------------------|
| `DRL_SESSION_TOKEN` | `session_token` (TokenBKNexus) |
| `DRL_USERNAME` | `username` (student ID) |
| `DRL_TELEGRAM_BOT_TOKEN` | `telegram_bot_token` |
| `DRL_TELEGRAM_CHAT_ID` | `telegram_chat_id` |

## Step 5 — Enable and test
1. Open the **Actions** tab. If prompted, click **"I understand my workflows, go ahead and enable them"**.
2. Select the **DRL Watcher** workflow on the left → **Run workflow** → **Run workflow** (one manual test run).
3. After ~1 minute, Telegram receives **"🤖 DRL bot started"**. 🎉 From now on it runs every 5 minutes.

---

## Managing from your phone

Message your bot (replies may be delayed up to ~5 minutes, since they wait for the next run):
`/status`, `/list`, `/check`, `/help`.

### When the bot reports an expired token
On GitHub Actions the token lives in a Secret, so update it like this (works from a phone):
1. Get a fresh `TokenBKNexus` (see the bookmarklet section in `DEPLOY_CLOUD.md`, or on a
   laptop: F12 → Cookies).
2. Go to the repo → **Settings → Secrets and variables → Actions → `DRL_SESSION_TOKEN` →
   Update** → paste the new value → Save.

(Sending `/token` to the bot while on Actions just reminds you to do the above — it can't
store the token itself.)

---

## Notes
- **Latency:** GitHub's minimum cron interval is 5 minutes and can be delayed further under
  load. Events that fill up within a few minutes may be missed. For faster (30-second)
  checks, use a server (see `DEPLOY_CLOUD.md`).
- **60-day pause:** GitHub disables scheduled workflows if the repo has no activity for 60
  days. The bot commits `state.json` when things change, which usually keeps it active; if
  it does get disabled, open the **Actions** tab and re-enable it (or **Run workflow** once).
- **Minutes:** unlimited free only while the repo is **Public**.
