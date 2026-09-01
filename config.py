import os
from dotenv import load_dotenv

load_dotenv()

# Bot token - Render environment variable or .env
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Admin IDs (comma separated in env)
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "123456789").split(",") if x.strip()]

# Required channel
REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "@aivora_uz")
REQUIRED_CHANNEL_ID = os.getenv("REQUIRED_CHANNEL_ID", "@aivora_uz")

# Admin username for contact
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "ABDRFV_11")

# Webhook settings for Render
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "")  # e.g. https://your-app.onrender.com
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}" if WEBHOOK_HOST else ""

PORT = int(os.getenv("PORT", 10000))

# Database
DATABASE_PATH = os.getenv("DATABASE_PATH", "database/bot.db")

# Default prices
DEFAULT_GEMINI_PRICE = 35000
DEFAULT_CHANNEL_PRICE = 100000
DEFAULT_CHANNEL_LINK = "https://t.me/+CBYCD-u8N7cwMDcy"

# Referral threshold
REFERRAL_THRESHOLD = 10
