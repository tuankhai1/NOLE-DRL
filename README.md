# DRL Watcher — bot theo dõi sự kiện đặt vé trên ctsv.hust.edu.vn

Bot gọi đúng API mà trang **"Đặt vé"** dùng (`/bknexus/Event/GetEvents`), vài chục giây một
lần, và **nhắn Telegram về điện thoại ngay** khi:

- 🎟️ Có **sự kiện mới** xuất hiện
- 🔔 Một sự kiện **chuyển sang "Đang mở đăng ký"** (quan trọng nhất để kịp giành slot)
- ♻️ Một sự kiện đang kín chỗ **vừa có slot trống trở lại**

Bot **chỉ báo**, bạn tự bấm vào đăng ký. Không cần mật khẩu trường.

---

## Cần cài gì

- **Python 3** (bạn đã có 3.14). Bot chỉ dùng thư viện chuẩn, **không cần pip install gì cả**.
- App **Telegram** trên điện thoại.

---

## Cài đặt 1 lần (khoảng 5 phút)

### Bước 1 — Tạo bot Telegram
1. Mở Telegram, tìm **@BotFather**, bấm **Start**.
2. Gửi `/newbot`, đặt tên và username (phải kết thúc bằng `bot`, ví dụ `drl_hust_bot`).
3. BotFather trả về một dòng **token** dạng `123456789:AAE...` → **copy** lại.
4. Bấm vào link bot vừa tạo và bấm **Start** (để bot được phép nhắn cho bạn).

### Bước 2 — Lấy `TokenBKNexus` và MSSV từ web
1. Mở trình duyệt, đăng nhập **https://ctsv.hust.edu.vn** như bình thường.
2. Nhấn **F12** → tab **Application** (Chrome/Edge) hoặc **Storage** (Firefox).
3. Bên trái: **Cookies** → chọn `https://ctsv.hust.edu.vn`.
4. Tìm dòng tên **`TokenBKNexus`** → copy toàn bộ giá trị (cột Value).
   - Tìm luôn dòng **`UserName`** (chính là MSSV của bạn) để điền cho khớp.

> Mẹo: token này thường sống khá lâu. Khi nào hết hạn, bot sẽ **tự nhắn Telegram báo bạn copy lại**.

### Bước 3 — Điền `config.json`
1. Copy file `config.example.json` thành `config.json` (cùng thư mục).
2. Mở `config.json`, điền:

```json
{
  "session_token": "<dán giá trị cookie TokenBKNexus>",
  "username": "<MSSV của bạn>",
  "telegram_bot_token": "<token từ BotFather>",
  "telegram_chat_id": "",
  "poll_seconds": 30,
  "notify_states": ["OPEN", "SOON"],
  "notify_new_any_state": true
}
```

3. **Lấy `telegram_chat_id`:** trong Telegram, gửi cho bot một tin bất kỳ (ví dụ "hi"),
   rồi ở thư mục này chạy:

   ```
   python drl_watch.py getchat
   ```

   Nó in ra `chat_id` (một dãy số) → dán vào `telegram_chat_id` trong `config.json`.

### Bước 4 — Kiểm tra
```
python drl_watch.py check    # phải in ra danh sách sự kiện -> token OK
python drl_watch.py test     # phải nhận được tin nhắn test trên Telegram
```

Nếu cả hai OK là xong.

---

## Chạy bot

Cách nhanh nhất: **bấm đúp `run.bat`** (hoặc chạy `python drl_watch.py run`).
Để cửa sổ đó mở là bot đang chạy. Lần đầu bot gửi 1 tin "đã khởi động".

### Các lệnh
| Lệnh | Tác dụng |
|------|----------|
| `python drl_watch.py run`     | Chạy vòng lặp theo dõi (mặc định) |
| `python drl_watch.py once`    | Kiểm tra 1 lần rồi thoát (cho Task Scheduler) |
| `python drl_watch.py check`   | In danh sách sự kiện hiện tại (test token) |
| `python drl_watch.py getchat` | Lấy `chat_id` Telegram |
| `python drl_watch.py test`    | Gửi 1 tin thử |

---

## Chạy nền, tự bật khi mở máy (khuyên dùng)

Để không phải nhớ bật thủ công, dùng **Task Scheduler** của Windows:

1. Mở **Task Scheduler** → **Create Task** (không phải Basic Task).
2. Tab **General**: đặt tên `DRL Watcher`; chọn **Run whether user is logged on or not**
   và tick **Run with highest privileges** (tùy chọn). Có thể tick **Hidden** để chạy ẩn.
3. Tab **Triggers** → **New** → **At log on** (hoặc At startup).
4. Tab **Actions** → **New**:
   - Program/script: đường dẫn `python.exe` của bạn
     (chạy `where python` trong CMD để lấy, ví dụ
     `C:\Users\tkng1\AppData\Local\Python\pythoncore-3.14-64\python.exe`)
   - Add arguments: `drl_watch.py run`
   - Start in: `D:\NTK\PROJECTS\DRL`
5. Tab **Settings**: tick **If the task fails, restart every** 1 minute, và
   **Do not stop** if runs long. OK.

> Lưu ý: máy phải **bật và có mạng** thì bot mới chạy. Nếu muốn chạy 24/7 kể cả khi tắt
> máy, cần đặt trên một máy luôn mở (VPS/Raspberry Pi…). Nói mình nếu bạn muốn hướng đó.

---

## Chỉnh nhanh

- **Báo dày/thưa hơn:** đổi `poll_seconds` (giây). Mặc định `30`. Đừng để quá nhỏ (<10).
- **Bớt báo sự kiện mới chưa mở:** đặt `notify_new_any_state` = `false` → chỉ báo
  sự kiện mới đang `OPEN`/`SOON`.

## File trong thư mục
- `drl_watch.py` — bot.
- `config.json` — cấu hình của bạn (chứa token, **không chia sẻ cho ai**).
- `config.example.json` — mẫu.
- `state.json` — bot tự tạo, nhớ các sự kiện đã thấy (xóa file này để "quên" và báo lại từ đầu).
- `run.bat` — bấm đúp để chạy.

## Khi token hết hạn
Bot sẽ nhắn Telegram "⚠️ Token hết hạn". Lúc đó làm lại **Bước 2** (copy `TokenBKNexus`
mới), dán vào `config.json`, chạy lại bot.
