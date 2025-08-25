# ForgeX Bot v0.0.2

Bot tự động phân tích price action trên MetaTrader 5 và gửi cảnh báo qua Telegram.

## 📦 Repository

**GitHub:** https://github.com/Peterxyjz/ForgeXBot.git

```bash
# Clone repository
git clone https://github.com/Peterxyjz/ForgeXBot.git
cd bot_moi
```

## 🚀 Hướng dẫn cài đặt nhanh

### Bước 1: Chuẩn bị
- **Python 3.8+** đã được cài đặt
- **MetaTrader 5** đã được cài đặt và đăng nhập
- **Telegram Bot Token** (xem hướng dẫn bên dưới)

### Bước 2: Clone và setup

```bash
# Clone repository
git clone https://github.com/Peterxyjz/ForgeXBot.git
cd bot_moi

# Auto setup
# Windows:
setup.bat
# Linux/Mac:
chmod +x setup.sh && ./setup.sh
```

### Bước 3: Cấu hình credentials

Chỉnh sửa file `.env` với thông tin của bạn:
```env
MT5_LOGIN=your_login
MT5_PASSWORD=your_password  
MT5_SERVER=your_server
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### Bước 4: Test và chạy

**Test bot:**
```bash
# Windows
test_bot.bat

# Linux/Mac
./test_bot.sh
```

**Chạy bot:**
```bash
# Windows
run_bot.bat

# Linux/Mac  
./run_bot.sh
```

## 🔧 Cài đặt thủ công (nếu cần)

```bash
# 1. Clone repository
git clone https://github.com/Peterxyjz/bot_moi.git
cd bot_moi

# 2. Tạo virtual environment
python -m venv venv

# 3. Kích hoạt venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Cài dependencies
pip install -r requirements.txt

# 5. Tạo file cấu hình
cp .env.example .env

# 6. Chỉnh sửa .env với credentials của bạn

# 7. Test
python main.py --test

# 8. Chạy
python main.py
```

## 📱 Tạo Telegram Bot

1. Nhắn tin cho [@BotFather](https://t.me/BotFather) trên Telegram
2. Gửi `/newbot` và làm theo hướng dẫn
3. Lưu **Bot Token** 
4. Gửi tin nhắn cho bot của bạn
5. Truy cập link này (thay YOUR_BOT_TOKEN):
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
6. Tìm **Chat ID** trong response JSON

## ⚙️ Tùy chỉnh

Chỉnh sửa `config/config.yaml` để:
- Thay đổi symbols giao dịch 
- Điều chỉnh timeframes
- Bật/tắt các patterns
- Cấu hình enhanced mode

## 🔍 Patterns được phát hiện

- **Bullish/Bearish Engulfing** - Nến nhấn chìm
- **Hammer** - Nến búa  
- **Shooting Star** - Sao băng
- **Doji** - Nến doji

## ⏰ Khung thời gian

- **M15** - 15 phút
- **H1** - 1 giờ
- **H4** - 4 giờ  
- **D1** - 1 ngày

## 📊 Symbols mặc định

- **XAUUSD.s** - Vàng
- **EURUSD.s** - Euro/USD
- **GBPUSD.s** - Bảng Anh/USD

## 📋 Yêu cầu hệ thống

- Windows 10+/Linux/macOS
- Python 3.8-3.11
- MetaTrader 5 
- 2GB RAM
- Kết nối internet ổn định

## 🆘 Khắc phục sự cố

**Lỗi kết nối MT5:**
- Kiểm tra MT5 đã đăng nhập chưa
- Verify login/password/server trong `.env`

**Lỗi Telegram:**  
- Kiểm tra Bot Token và Chat ID
- Đảm bảo đã gửi tin nhắn cho bot trước

**Lỗi Python/Dependencies:**
- Sử dụng Python 3.8-3.11
- Chạy lại `pip install -r requirements.txt`

## 🤝 Đóng góp

Mọi đóng góp đều được hoan nghênh! Hãy:
1. Fork repository
2. Tạo branch mới (`git checkout -b feature/amazing-feature`)
3. Commit thay đổi (`git commit -m 'Add amazing feature'`)
4. Push lên branch (`git push origin feature/amazing-feature`)
5. Tạo Pull Request

## 📄 License

Dự án này được phát hành dưới MIT License - xem file [LICENSE](LICENSE) để biết thêm chi tiết.

---
**⚠️ Lưu ý:** Bot chỉ phục vụ mục đích phân tích, không phải lời khuyên đầu tư.
