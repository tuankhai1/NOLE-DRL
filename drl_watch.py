#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DRL watcher - theo doi su kien dat ve tren ctsv.hust.edu.vn va bao ve Telegram.

Khong can mat khau truong. Bot dung Token phien (cookie TokenBKNexus) + UserName (MSSV)
ma ban tu copy tu trinh duyet sau khi dang nhap web.

Lenh:
    python drl_watch.py run       # chay vong lap theo doi (mac dinh)
    python drl_watch.py once      # kiem tra 1 lan roi thoat (dung cho Task Scheduler)
    python drl_watch.py check     # goi API 1 lan, in danh sach su kien (kiem tra token)
    python drl_watch.py getchat   # lay chat_id Telegram (sau khi ban nhan tin cho bot)
    python drl_watch.py test      # gui 1 tin nhan thu qua Telegram
"""
import json
import os
import sys
import time
import datetime
import urllib.request
import urllib.error
import urllib.parse

API_BASE = "https://ctsv.hust.edu.vn/bknexus/"
WEB_URL = "https://ctsv.hust.edu.vn/dat-ve"

# Console Windows mac dinh cp1252 -> khong in duoc tieng Viet/emoji. Ep UTF-8.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "config.json")
STATE_PATH = os.path.join(HERE, "state.json")

STATE_LABEL = {
    "OPEN": "Dang mo dang ky",
    "SOON": "Chua mo dang ky",
    "FULL": "Da het cho",
    "CLOSED": "Da dong dang ky",
    "ENDED": "Da dien ra",
    "DRAFT": "Nhap",
}
STATE_EMOJI = {
    "OPEN": "\U0001F7E2",   # green circle
    "SOON": "\U0001F535",   # blue circle
    "FULL": "\U0001F534",   # red circle
    "CLOSED": "\U0001F7E3", # purple circle
    "ENDED": "⚪",       # white circle
    "DRAFT": "⚪",
}


LOG_PATH = os.path.join(HERE, "drl_watch.log")


def log(*args):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = ts + " " + " ".join(str(a) for a in args)
    print(line, flush=True)
    try:
        # xoay log khi qua 1MB de khong phinh to
        if os.path.exists(LOG_PATH) and os.path.getsize(LOG_PATH) > 1_000_000:
            os.replace(LOG_PATH, LOG_PATH + ".old")
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except Exception as e:
        log("Loi doc", path, "->", e)
        return default


def save_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


# Chay tren GitHub Actions? (anh huong cach xu ly lenh /token)
IS_ACTIONS = os.environ.get("GITHUB_ACTIONS") == "true"

# Cho phep cau hinh qua bien moi truong (dung cho GitHub Actions Secrets).
ENV_MAP = {
    "session_token": "DRL_SESSION_TOKEN",
    "username": "DRL_USERNAME",
    "telegram_bot_token": "DRL_TELEGRAM_BOT_TOKEN",
    "telegram_chat_id": "DRL_TELEGRAM_CHAT_ID",
}


def load_config(need=("session_token", "username", "telegram_bot_token", "telegram_chat_id")):
    cfg = load_json(CONFIG_PATH, {}) or {}
    # Bien moi truong ghi de len config.json (neu co)
    for key, env in ENV_MAP.items():
        val = os.environ.get(env)
        if val not in (None, ""):
            cfg[key] = val
    if os.environ.get("DRL_POLL_SECONDS"):
        try:
            cfg["poll_seconds"] = int(os.environ["DRL_POLL_SECONDS"])
        except ValueError:
            pass

    missing = [k for k in need if not str(cfg.get(k, "")).strip()]
    if missing:
        log("Thieu cau hinh:", ", ".join(missing),
            "- dien vao config.json hoac dat bien moi truong DRL_* tuong ung.")
        sys.exit(1)
    cfg.setdefault("poll_seconds", 30)
    cfg.setdefault("notify_states", ["OPEN", "SOON"])
    cfg.setdefault("notify_new_any_state", True)
    return cfg


def save_config(cfg):
    """Ghi lai config.json (dung khi cap nhat token qua Telegram)."""
    out = {k: cfg[k] for k in (
        "session_token", "username", "telegram_bot_token", "telegram_chat_id",
        "poll_seconds", "notify_states", "notify_new_any_state") if k in cfg}
    save_json(CONFIG_PATH, out)


# ----------------------------- HTTP ---------------------------------------

def http_post_json(url, payload, cookie=None, timeout=25):
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Origin": "https://ctsv.hust.edu.vn",
        "Referer": WEB_URL,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DRL-watch/1.0",
    }
    if cookie:
        headers["Cookie"] = cookie
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
            code = resp.getcode()
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        code = e.code
    except Exception as e:
        return {"_neterror": str(e)}
    try:
        obj = json.loads(raw)
        obj["_http"] = code
        return obj
    except Exception:
        return {"_http": code, "RespCode": -999, "RespText": "Phan hoi khong phai JSON",
                "_raw": raw[:400]}


def get_events(cfg):
    """Goi Event/GetEvents. Tra ve (events_list, error_str_or_None)."""
    cookie = "TokenBKNexus=%s; UserName=%s" % (cfg["session_token"], cfg["username"])
    payload = {"Token": cfg["session_token"], "UserName": cfg["username"]}
    res = http_post_json(API_BASE + "Event/GetEvents", payload, cookie=cookie)

    if "_neterror" in res:
        return None, "net:" + res["_neterror"]
    rc = res.get("RespCode")
    if rc == 0:
        return res.get("Events") or [], None
    if rc in (401, 104, 105) or res.get("_http") == 401:
        return None, "auth:" + str(res.get("RespText") or "Phien dang nhap khong hop le (token het han)")
    return None, "api:RespCode=%s %s" % (rc, res.get("RespText") or "")


# --------------------------- Telegram -------------------------------------

def tg_api(cfg, method, params):
    url = "https://api.telegram.org/bot%s/%s" % (cfg["telegram_bot_token"], method)
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8", "replace"))
        except Exception:
            return {"ok": False, "error": "http %s" % e.code}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def tg_send(cfg, text, silent=False):
    for attempt in range(3):
        res = tg_api(cfg, "sendMessage", {
            "chat_id": cfg["telegram_chat_id"],
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": "true",
            "disable_notification": "true" if silent else "false",
        })
        if res.get("ok"):
            return True
        log("Telegram loi (lan %d):" % (attempt + 1), res.get("description") or res.get("error"))
        time.sleep(2 * (attempt + 1))
    return False


def esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def tg_get_updates(cfg, offset):
    res = tg_api(cfg, "getUpdates", {
        "offset": offset, "timeout": 0, "allowed_updates": '["message"]'})
    if not res.get("ok"):
        return []
    return res.get("result", [])


HELP_TEXT = (
    "\U0001F916 <b>Lenh bot DRL</b>\n"
    "/status - tinh trang bot (token con ok khong, bao nhieu su kien)\n"
    "/list - cac su kien dang mo dang ky ngay bay gio\n"
    "/check - kiem tra ngay lap tuc\n"
    "/token &lt;gia_tri&gt; - cap nhat TokenBKNexus moi (khi token het han)\n"
    "/mssv &lt;mssv&gt; - cap nhat ma so sinh vien\n"
    "/help - xem lai danh sach lenh"
)


def process_commands(cfg, state):
    """Doc lenh gui toi bot tu Telegram va xu ly. Chi nhan tu dung chat_id."""
    offset = int(state.get("tg_offset", 0))
    updates = tg_get_updates(cfg, offset + 1 if offset else 0)
    did = False
    for upd in updates:
        state["tg_offset"] = upd.get("update_id", offset)
        did = True
        msg = upd.get("message") or {}
        chat = msg.get("chat") or {}
        if str(chat.get("id")) != str(cfg["telegram_chat_id"]):
            continue  # bo qua nguoi la
        text = (msg.get("text") or "").strip()
        if not text.startswith("/"):
            continue
        parts = text.split(None, 1)
        cmd = parts[0].lower().split("@")[0]
        arg = parts[1].strip() if len(parts) > 1 else ""

        if cmd in ("/start", "/help"):
            tg_send(cfg, HELP_TEXT)
        elif cmd == "/status":
            tg_send(cfg, cmd_status_text(cfg, state))
        elif cmd == "/list":
            tg_send(cfg, cmd_list_text(cfg))
        elif cmd == "/check":
            tg_send(cfg, "\U0001F50D Dang kiem tra...")
            poll_once(cfg, state)
            tg_send(cfg, "✅ Da kiem tra xong. " + cmd_list_text(cfg))
        elif cmd == "/token":
            if not arg:
                tg_send(cfg, "Cu phap: <code>/token GIA_TRI_TokenBKNexus</code>")
            elif IS_ACTIONS:
                tg_send(cfg,
                        "ℹ️ Bot dang chay tren GitHub Actions nen khong luu token "
                        "truc tiep duoc.\nHay vao repo tren GitHub: <b>Settings → Secrets and "
                        "variables → Actions → DRL_SESSION_TOKEN → Update</b>, "
                        "dan gia tri moi vao do (lam tren dien thoai duoc).")
            else:
                cfg["session_token"] = arg.split()[0]
                save_config(cfg)
                state["last_auth_alert"] = 0
                save_json(STATE_PATH, state)
                ev, err = get_events(cfg)
                if err:
                    tg_send(cfg, "⚠️ Da luu token nhung van loi: " + esc(err))
                else:
                    tg_send(cfg, "✅ Da cap nhat token. Doc duoc %d su kien. Bot chay tiep binh thuong." % len(ev))
        elif cmd == "/mssv":
            if not arg:
                tg_send(cfg, "Cu phap: <code>/mssv 20xxxxxx</code>")
            else:
                cfg["username"] = arg.split()[0]
                save_config(cfg)
                tg_send(cfg, "✅ Da cap nhat MSSV: " + esc(cfg["username"]))
        else:
            tg_send(cfg, "Khong hieu lenh. Go /help de xem cac lenh.")
    if did:
        save_json(STATE_PATH, state)


def cmd_status_text(cfg, state):
    has_token = bool(str(cfg.get("session_token", "")).strip())
    if not has_token:
        return ("⚠️ Chua co token. Gui /token &lt;gia_tri&gt; de bot bat dau.\n"
                "MSSV hien tai: " + esc(cfg.get("username") or "(chua co)"))
    ev, err = get_events(cfg)
    if err:
        if err.startswith("auth"):
            return "⚠️ Token het han/khong hop le. Gui /token &lt;gia_tri_moi&gt;."
        return "⚠️ Loi: " + esc(err)
    opening = [e for e in ev if e.get("State") == "OPEN"]
    known = state.get("events", {})
    return ("✅ Bot dang chay binh thuong.\n"
            "Theo doi: <b>%d</b> su kien (da ghi nho %d).\n"
            "Dang mo dang ky: <b>%d</b>\n"
            "Chu ky kiem tra: %ds/lan." % (len(ev), len(known), len(opening), cfg["poll_seconds"]))


def cmd_list_text(cfg):
    ev, err = get_events(cfg)
    if err:
        return "⚠️ " + esc(err)
    opening = [e for e in ev if e.get("State") == "OPEN"]
    if not opening:
        return "Hien khong co su kien nao dang mo dang ky."
    return "\U0001F39F️ <b>Dang mo dang ky (%d):</b>\n\n" % len(opening) + "\n\n".join(
        event_block(e, "•") for e in opening[:8]) + "\n\n\U0001F517 " + WEB_URL


# --------------------------- Format ---------------------------------------

def fmt_time(s):
    if not s:
        return ""
    s = str(s).replace("T", " ")
    date = s[:10].split("-")
    if len(date) != 3:
        return s
    hm = s[11:16]
    return (hm + " " if hm else "") + "%s/%s/%s" % (date[2], date[1], date[0])


def time_range(ev):
    start = fmt_time(ev.get("StartTime"))
    end = ev.get("EndTime")
    if not end:
        return start
    same_day = str(ev.get("StartTime", ""))[:10] == str(end)[:10]
    end_fmt = str(end)[11:16] if same_day else fmt_time(end)
    return "%s – %s" % (start, end_fmt) if start else end_fmt


def event_block(ev, header):
    st = ev.get("State", "")
    emoji = STATE_EMOJI.get(st, "•")
    label = STATE_LABEL.get(st, st)
    lines = ["%s <b>%s</b>" % (header, esc(ev.get("Title", "(khong ten)")))]
    if ev.get("GroupName"):
        lines.append("\U0001F4C1 %s" % esc(ev["GroupName"]))
    tr = time_range(ev)
    if tr:
        lines.append("\U0001F550 %s" % esc(tr))
    if ev.get("Location"):
        lines.append("\U0001F4CD %s" % esc(ev["Location"]))
    cap = ev.get("Capacity")
    reg = ev.get("Registered")
    rem = ev.get("Remaining")
    if cap:
        slot = "\U0001F39F️ Con %s/%s cho" % (
            rem if rem is not None else "?", cap)
        if reg is not None:
            slot += " (da dang ky %s)" % reg
        lines.append(slot)
    lines.append("%s Trang thai: <b>%s</b>" % (emoji, esc(label)))
    if ev.get("MyTicket"):
        lines.append("✅ Ban DA co ve su kien nay")
    return "\n".join(lines)


# --------------------------- Core logic -----------------------------------

def event_key(ev):
    return str(ev.get("Id"))


def is_bookable(ev):
    if ev.get("State") != "OPEN":
        return False
    if ev.get("BlockedBy"):
        return False
    cap = ev.get("Capacity") or 0
    rem = ev.get("Remaining")
    if cap and rem is not None:
        return rem > 0
    return True


def poll_once(cfg, state):
    events, err = get_events(cfg)
    now = time.time()

    if err:
        if err.startswith("auth:"):
            last = state.get("last_auth_alert", 0)
            if now - last > 3 * 3600:  # canh bao toi da moi 3 gio
                tg_send(cfg,
                        "⚠️ <b>Token het han</b>\n"
                        "Bot khong truy cap duoc ctsv nua. Hay dang nhap lai web, "
                        "copy cookie <code>TokenBKNexus</code> moi vao config.json roi chay lai.\n"
                        "Chi tiet: " + esc(err[5:]))
                state["last_auth_alert"] = now
                save_json(STATE_PATH, state)
            log("AUTH:", err)
        else:
            log("Loi poll (bo qua, thu lai sau):", err)
        return

    # thanh cong -> reset canh bao auth
    if state.get("last_auth_alert"):
        state["last_auth_alert"] = 0

    known = state.setdefault("events", {})  # key -> {state, remaining, title}
    first_run = not state.get("initialized")

    notes = []  # (header, event) can bao
    for ev in events:
        k = event_key(ev)
        cur = {
            "state": ev.get("State"),
            "remaining": ev.get("Remaining"),
            "title": ev.get("Title"),
        }
        prev = known.get(k)

        if prev is None:
            if not first_run:
                if ev.get("State") == "OPEN" and is_bookable(ev):
                    notes.append(("\U0001F39F️ <b>SU KIEN MOI - DANG MO DANG KY</b>", ev))
                elif cfg["notify_new_any_state"] or ev.get("State") in cfg["notify_states"]:
                    notes.append(("\U0001F195 <b>SU KIEN MOI</b>", ev))
        else:
            # chuyen sang OPEN (quan trong nhat - canh slot)
            if prev.get("state") != "OPEN" and ev.get("State") == "OPEN":
                notes.append(("\U0001F514 <b>DA MO DANG KY</b>", ev))
            # slot vua duoc nha ra (FULL -> con cho, van OPEN)
            elif (ev.get("State") == "OPEN" and is_bookable(ev)
                  and (prev.get("remaining") == 0)
                  and (ev.get("Remaining") or 0) > 0):
                notes.append(("♻️ <b>VUA CO SLOT TRONG</b>", ev))

        known[k] = cur

    # don dep su kien bien mat (tuy chon - giu lai cho gon)
    live_keys = {event_key(e) for e in events}
    for k in list(known.keys()):
        if k not in live_keys:
            known.pop(k, None)

    if first_run:
        state["initialized"] = True
        open_now = [e for e in events if e.get("State") == "OPEN"]
        summary = ("\U0001F916 <b>Bot DRL da khoi dong</b>\n"
                   "Dang theo doi <b>%d</b> su kien (moi %ds/lan).\n"
                   "Dang mo dang ky ngay bay gio: <b>%d</b>" % (
                       len(events), cfg["poll_seconds"], len(open_now)))
        if open_now:
            summary += "\n\n" + "\n\n".join(
                event_block(e, "\U0001F39F️") for e in open_now[:5])
        summary += "\n\n\U0001F517 %s" % WEB_URL
        tg_send(cfg, summary, silent=True)
        log("Khoi tao baseline: %d su kien, %d dang mo." % (len(events), len(open_now)))
    else:
        for header, ev in notes:
            msg = event_block(ev, header) + "\n\n\U0001F449 Vao dat ve: %s" % WEB_URL
            ok = tg_send(cfg, msg)
            log(("DA BAO" if ok else "BAO LOI"), "-", ev.get("Title"))
        if not notes:
            log("Khong co thay doi. (%d su kien)" % len(events))

    save_json(STATE_PATH, state)


# --------------------------- Commands -------------------------------------

def has_credentials(cfg):
    return bool(str(cfg.get("session_token", "")).strip()
                and str(cfg.get("username", "")).strip())


def cmd_run(cfg):
    state = load_json(STATE_PATH, {})
    interval = max(10, int(cfg["poll_seconds"]))
    log("Bat dau theo doi. Chu ky %ds. Ctrl+C de dung." % interval)
    if not has_credentials(cfg):
        log("Chua co session_token/username - cho lenh /token tu Telegram.")
        tg_send(cfg, "\U0001F916 Bot da chay nhung <b>chua co token truong</b>.\n"
                     "Gui <code>/token GIA_TRI_TokenBKNexus</code> va "
                     "<code>/mssv MSSV</code> de bat dau. Go /help de xem huong dan.")
    while True:
        try:
            # luon lang nghe lenh Telegram (ke ca khi chua co token)
            process_commands(cfg, state)
            if has_credentials(cfg):
                poll_once(cfg, state)
        except KeyboardInterrupt:
            log("Dung theo doi.")
            break
        except Exception as e:
            log("Loi khong mong doi (tiep tuc):", repr(e))
        try:
            time.sleep(interval)
        except KeyboardInterrupt:
            log("Dung theo doi.")
            break


def cmd_once(cfg):
    state = load_json(STATE_PATH, {})
    # nghe lenh Telegram mot luot (phuc vu /status, /list... khi chay tren Actions)
    try:
        process_commands(cfg, state)
    except Exception as e:
        log("Loi doc lenh Telegram (bo qua):", repr(e))
    poll_once(cfg, state)


def cmd_check(cfg):
    events, err = get_events(cfg)
    if err:
        log("LOI:", err)
        if err.startswith("auth"):
            log("-> Token sai/het han. Copy lai cookie TokenBKNexus tu trinh duyet.")
        return
    log("OK - %d su kien:" % len(events))
    for e in events:
        print("  [%-6s] %-45s | con %s/%s | %s" % (
            e.get("State"), str(e.get("Title"))[:45],
            e.get("Remaining"), e.get("Capacity"), fmt_time(e.get("StartTime"))))


def cmd_getchat(cfg):
    res = tg_api(cfg, "getUpdates", {})
    if not res.get("ok"):
        log("Loi:", res.get("description") or res.get("error"))
        log("Kiem tra telegram_bot_token trong config.json co dung khong.")
        return
    seen = {}
    for upd in res.get("result", []):
        msg = upd.get("message") or upd.get("channel_post") or {}
        chat = msg.get("chat") or {}
        if chat.get("id") is not None:
            seen[chat["id"]] = chat.get("title") or (
                (chat.get("first_name", "") + " " + chat.get("last_name", "")).strip()
                or chat.get("username") or chat.get("type"))
    if not seen:
        log("Chua thay tin nhan nao. Hay mo Telegram, tim bot cua ban va bam START / nhan 1 tin, roi chay lai lenh nay.")
        return
    log("Cac chat_id tim thay (dien vao config.json -> telegram_chat_id):")
    for cid, name in seen.items():
        print("   %s  <-  %s" % (cid, name))


def cmd_test(cfg):
    ok = tg_send(cfg, "✅ <b>Test DRL bot</b>\nNeu ban thay tin nhan nay, Telegram da OK!")
    log("Gui thu:", "THANH CONG" if ok else "THAT BAI")


def main():
    cmd = (sys.argv[1] if len(sys.argv) > 1 else "run").lower()
    if cmd == "getchat":
        cfg = load_config(need=("telegram_bot_token",))
    elif cmd in ("test", "run"):
        # run co the bootstrap token qua Telegram nen chi can thong tin Telegram
        cfg = load_config(need=("telegram_bot_token", "telegram_chat_id"))
    else:
        cfg = load_config()
    {
        "run": cmd_run,
        "once": cmd_once,
        "check": cmd_check,
        "getchat": cmd_getchat,
        "test": cmd_test,
    }.get(cmd, cmd_run)(cfg)


if __name__ == "__main__":
    main()
