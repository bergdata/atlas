# Telegram Integration - Atlas EC2

All Telegram functionality has been consolidated into `Functions/telegram_notifier.py` for simplicity.

## Quick Start

1. **Set up your bot token** in `.env` file:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

2. **Run setup** to get your chat ID:
   ```bash
   python Functions/telegram_notifier.py setup
   store the chat_ID in config.py
   ```

3. **Send a message** to your bot on Telegram

4. **Setup will complete** and save your chat ID automatically

## Usage Modes

### Setup Mode
```bash
python Functions/telegram_notifier.py setup
```
- Automatically detects your chat ID
- Sends a test message to verify everything works
- Saves chat ID to config for future use

### Debug Mode
```bash
python Functions/telegram_notifier.py debug
```
- Tests bot connection
- Shows recent messages/updates
- Checks webhook status
- Helps troubleshoot issues

### Set Chat ID Manually
```bash
python Functions/telegram_notifier.py set 123456789
```
- Manually set a known chat ID
- Verifies it works by sending a test message
- Saves to config

### Default Mode (Example Usage)
```bash
python Functions/telegram_notifier.py
```
- Runs example usage
- Sends test messages if chat ID is configured

## In Your Code

```python
from Functions.telegram_notifier import send_to_phone, TelegramNotifier

# Quick message
send_to_phone("Hello from Atlas EC2!")

# Or use the class
notifier = TelegramNotifier()
notifier.send_message("Another message")
```

## What Was Consolidated

- ✅ `setup_telegram.py` → `telegram_notifier.py setup`
- ✅ `debug_telegram.py` → `telegram_notifier.py debug`  
- ✅ `set_chat_id.py` → `telegram_notifier.py set <id>`
- ✅ All functionality now in one file!

Much cleaner and easier to maintain! 🎉
