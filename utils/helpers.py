from config import ADMIN_IDS
from database.db import get_setting


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def format_price(price: int) -> str:
    return f"{price:,}".replace(",", " ")


async def get_admin_username() -> str:
    return await get_setting("admin_username", "ABDRFV_11")


async def check_channel_member(bot, user_id: int, channel: str) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False
