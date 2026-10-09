# Đưa bot lên máy chủ đám mây miễn phí (chạy 24/7, không cần laptop)

Mục tiêu: bot sống trên một máy chủ luôn bật. Bạn tắt laptop, cất đi — bot vẫn canh và
nhắn Telegram về điện thoại. **Setup lần đầu làm trên laptop (~20–30 phút, một lần).**
Sau đó quản lý hoàn toàn bằng điện thoại qua các lệnh Telegram.

Hướng dẫn dùng **Oracle Cloud Always Free** (miễn phí vĩnh viễn, mạnh nhất trong các gói
free). Nhưng **bất kỳ máy chủ Ubuntu nào cũng chạy y hệt** — nếu bạn có sẵn VPS khác,
nhảy tới [Phần B](#phần-b--cài-bot-lên-máy-chủ).

---

## Phần A — Tạo máy chủ miễn phí (Oracle Cloud)

> Oracle yêu cầu một thẻ (Visa/Mastercard, kể cả thẻ ảo) để **xác minh danh tính** —
> **không bị trừ tiền** với gói Always Free. Nếu không có thẻ, báo mình để chọn hướng khác.

1. Vào https://www.oracle.com/cloud/free/ → **Start for free**, đăng ký (email, chọn
   quốc gia **Vietnam**, xác minh điện thoại + thẻ).
2. Sau khi vào **Oracle Cloud Console**: menu ☰ → **Compute** → **Instances** →
   **Create instance**.
3. Đặt:
   - **Image**: Canonical **Ubuntu 22.04** (hoặc 24.04).
   - **Shape**: bấm **Change shape** → chọn **Ampere (ARM)** `VM.Standard.A1.Flex`
     (1 OCPU, 6 GB là thừa) — đây là phần Always Free. Nếu ARM báo hết chỗ, chọn
     **VM.Standard.E2.1.Micro** (AMD, cũng Always Free).
   - **Add SSH keys**: chọn **Generate a key pair for me** → bấm **Save private key**
     (tải file `.key` về laptop — giữ kỹ, dùng để đăng nhập).
4. **Create**. Chờ ~1 phút tới khi trạng thái **RUNNING**. Ghi lại **Public IP address**.
5. Mở cổng mạng cho... *không cần* — bot chỉ gọi ra ngoài, không mở cổng vào. Bỏ qua.

---

## Phần B — Cài bot lên máy chủ

Làm trên **laptop** (nơi đang có thư mục `D:\NTK\PROJECTS\DRL`). Mở **PowerShell**.

### 1. Đăng nhập thử vào máy chủ
Thay `<KEY>` = đường dẫn file private key vừa tải, `<IP>` = Public IP:
```powershell
ssh -i "<KEY>" ubuntu@<IP>
```
Lần đầu gõ `yes`. Vào được (thấy dấu nhắc `ubuntu@...`) là OK. Gõ `exit` để ra.

> Oracle Ubuntu đăng nhập bằng user **`ubuntu`**. (VPS khác có thể là `root` hoặc tên khác.)

### 2. Copy bot + cấu hình lên máy chủ
Chạy ở thư mục dự án trên laptop (cd vào `D:\NTK\PROJECTS\DRL` trước):
```powershell
scp -i "<KEY>" drl_watch.py config.json deploy/setup.sh ubuntu@<IP>:~
```
Lệnh này đẩy 3 file (kèm `config.json` đã có sẵn token của bạn) lên máy chủ.

### 3. Cài đặt (tự tạo dịch vụ chạy nền)
```powershell
ssh -i "<KEY>" ubuntu@<IP> "bash ~/setup.sh"
```
Script sẽ cài `drl_watch.py` vào `~/drl`, tạo dịch vụ systemd `drl-watch`, bật chạy ngay
và **tự khởi động lại khi reboot / khi lỗi**. Cuối màn hình phải thấy dòng
`Active: active (running)`.

Trong vài giây, Telegram của bạn sẽ nhận tin **"🤖 Bot DRL đã khởi động"**. Xong! 🎉
Giờ có thể tắt laptop — bot chạy độc lập trên mây.

---

## Quản lý bằng điện thoại (không cần laptop nữa)

Nhắn thẳng cho bot **@noledrl_bot** trên Telegram:

| Lệnh | Tác dụng |
|------|----------|
| `/status` | Bot còn sống không, token còn hạn không, đang theo dõi mấy sự kiện |
| `/list` | Các sự kiện **đang mở đăng ký** ngay bây giờ |
| `/check` | Bắt bot kiểm tra ngay lập tức |
| `/token <giá trị>` | Cập nhật token trường mới (khi hết hạn) |
| `/mssv <mssv>` | Đổi mã số sinh viên |
| `/help` | Xem lại danh sách lệnh |

### Khi bot báo "⚠️ Token hết hạn" — cách lấy token mới bằng điện thoại

Token trường (`TokenBKNexus`) đọc được từ cookie trình duyệt. Trên điện thoại:

**Cách dễ (bookmarklet — làm 1 lần):**
1. Tạo một bookmark bất kỳ trong trình duyệt điện thoại, rồi **sửa địa chỉ** của bookmark
   đó thành đúng đoạn sau (dán nguyên văn):
   ```
   javascript:(function(){var m=document.cookie.match(/TokenBKNexus=([^;]+)/);if(!m){alert('Chua dang nhap ctsv');return;}prompt('Copy dong duoi roi gui cho bot:','/token '+m[1]);})();
   ```
2. Khi cần token mới: mở **https://ctsv.hust.edu.vn** trên điện thoại, **đăng nhập**, rồi
   mở bookmark vừa tạo. Nó hiện sẵn dòng `/token xxxxx` → copy.
3. Dán dòng đó gửi cho bot **@noledrl_bot**. Bot trả lời "✅ Đã cập nhật token".

> Safari (iPhone): bookmark → Edit → dán vào ô địa chỉ. Chrome (Android): lưu bookmark rồi
> vào Bookmarks sửa URL. Nếu trình duyệt chặn `javascript:` thì làm "cách thủ công" dưới.

**Cách thủ công (khi rảnh có laptop):** làm lại Bước 2 trong `README.md` (F12 → Cookies →
copy `TokenBKNexus`), rồi gửi `/token <giá trị>` cho bot. Token thường sống khá lâu nên
việc này ít khi phải làm.

---

## Kiểm tra / xử lý trên máy chủ (khi cần, qua SSH)

```bash
systemctl status drl-watch        # trạng thái
journalctl -u drl-watch -f        # xem log chạy trực tiếp (Ctrl+C để thoát)
sudo systemctl restart drl-watch  # khởi động lại
sudo systemctl disable --now drl-watch   # dừng hẳn
```

Cập nhật bot (nếu sau này mình sửa code): copy `drl_watch.py` mới lên rồi:
```bash
cp ~/drl_watch.py ~/drl/drl_watch.py && sudo systemctl restart drl-watch
```

---

## Lưu ý bảo mật
- `config.json` trên máy chủ chứa `TokenBKNexus` + token Telegram. Máy chủ là của riêng
  bạn nên ổn, nhưng đừng chia sẻ quyền SSH / file này cho người khác.
- Giữ kỹ file private key (`.key`). Mất nó = mất đường vào máy chủ (phải tạo lại).
