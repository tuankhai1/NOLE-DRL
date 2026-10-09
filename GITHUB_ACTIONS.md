# Chạy bot bằng GitHub Actions (miễn phí, KHÔNG cần thẻ, không cần laptop)

Bot chạy trên hạ tầng của GitHub, **mỗi ~5 phút kiểm tra một lần** (giới hạn nhỏ nhất
GitHub cho phép; đôi khi trễ thêm vài phút). Token và thông tin nhạy cảm cất trong
**Secrets** của GitHub — **không nằm trong mã nguồn**.

> ⚠️ Repo để **Public** thì GitHub Actions **miễn phí không giới hạn phút chạy**. Để
> Private sẽ bị giới hạn 2000 phút/tháng — không đủ cho chu kỳ 5 phút. Mã nguồn không chứa
> bí mật nào (bí mật nằm trong Secrets) nên để Public là an toàn.

---

## Bước 1 — Có tài khoản GitHub
Chưa có thì đăng ký tại https://github.com (miễn phí, chỉ cần email).

## Bước 2 — Tạo repo rỗng
1. https://github.com/new
2. **Repository name**: `drl-watch`
3. Chọn **Public**.
4. **KHÔNG** tick "Add a README" (để trống hoàn toàn).
5. **Create repository**. Ghi lại địa chỉ dạng `https://github.com/<tên-bạn>/drl-watch.git`.

## Bước 3 — Đẩy mã nguồn lên

### Cách A — Dùng Git (khuyên dùng; mình đã chuẩn bị sẵn repo cục bộ)
Mở **PowerShell**, ở thư mục `D:\NTK\PROJECTS\DRL`, chạy (thay `<URL>` = địa chỉ repo ở Bước 2):
```powershell
git remote add origin <URL>
git push -u origin main
```
Lần đầu push sẽ hiện cửa sổ đăng nhập GitHub trên trình duyệt → đăng nhập là xong.
(Mình đã cấu hình để `config.json` **không** bị đẩy lên — chỉ có code + workflow.)

### Cách B — Không cần Git, dùng web
1. Trong repo vừa tạo → **Add file → Upload files** → kéo **`drl_watch.py`** vào → **Commit**.
2. **Add file → Create new file** → ô tên gõ: `.github/workflows/watch.yml` → dán toàn bộ
   nội dung file `watch.yml` (lấy từ thư mục `D:\NTK\PROJECTS\DRL\.github\workflows\`) →
   **Commit**.
3. **Tuyệt đối không** upload `config.json`.

## Bước 4 — Nạp Secrets (thông tin bí mật)
Trong repo: **Settings → Secrets and variables → Actions → New repository secret**. Tạo
**4 secret** (tên viết đúng y hệt), giá trị copy từ file `config.json` của bạn:

| Tên secret | Giá trị (lấy trong config.json) |
|------------|--------------------------------|
| `DRL_SESSION_TOKEN` | `session_token` (TokenBKNexus) |
| `DRL_USERNAME` | `username` (MSSV) |
| `DRL_TELEGRAM_BOT_TOKEN` | `telegram_bot_token` |
| `DRL_TELEGRAM_CHAT_ID` | `telegram_chat_id` |

## Bước 5 — Bật và chạy thử
1. Mở tab **Actions**. Nếu hỏi, bấm **"I understand my workflows, go ahead and enable them"**.
2. Chọn workflow **DRL Watcher** bên trái → bấm **Run workflow** → **Run workflow** (chạy tay 1 lần để test).
3. Sau ~1 phút, Telegram nhận tin **"🤖 Bot DRL đã khởi động"**. 🎉 Từ giờ nó tự chạy mỗi 5 phút.

---

## Quản lý bằng điện thoại

Nhắn cho **@noledrl_bot** (phản hồi có thể trễ tới ~5 phút vì chờ lần chạy kế tiếp):
`/status`, `/list`, `/check`, `/help`.

### Khi bot báo token hết hạn
Trên GitHub Actions, token nằm trong Secret nên cập nhật như sau (làm trên điện thoại được):
1. Lấy `TokenBKNexus` mới (xem mục bookmarklet trong `DEPLOY_CLOUD.md`, hoặc dùng laptop:
   F12 → Cookies).
2. Vào repo → **Settings → Secrets and variables → Actions → `DRL_SESSION_TOKEN` →
   Update** → dán giá trị mới → Save.

(Gửi `/token` cho bot khi chạy trên Actions sẽ chỉ nhắc bạn làm bước trên, không tự lưu được.)

---

## Lưu ý
- **Độ trễ:** GitHub chạy cron tối thiểu 5 phút và có thể trễ thêm khi hệ thống bận. Sự kiện
  nào hết slot trong vài phút thì có thể lỡ. Cần nhanh hơn (30 giây) thì phải dùng máy chủ
  (xem `DEPLOY_CLOUD.md`).
- **Tạm dừng sau 60 ngày:** GitHub tự tắt lịch chạy nếu repo không có hoạt động 60 ngày.
  Bot tự commit `state.json` khi có thay đổi nên thường không sao; nếu lỡ bị tắt, vào tab
  **Actions** bấm bật lại (hoặc **Run workflow** một lần).
- **Phút chạy:** chỉ miễn phí vô hạn khi repo **Public**.
