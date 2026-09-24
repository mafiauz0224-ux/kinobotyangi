from aiogram import Bot
from config import CHANNEL_ID, ADMIN_IDS


async def is_subscribed(bot: Bot, user_id: int) -> bool:
    if user_id in ADMIN_IDS:
        return True
    if not CHANNEL_ID:
        return True
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False
