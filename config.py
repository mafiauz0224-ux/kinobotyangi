import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]
CHANNEL_ID = os.getenv("CHANNEL_ID") or None
CHANNEL_LINK = os.getenv("CHANNEL_LINK") or None
