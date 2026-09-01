from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def main_menu_kb(is_admin: bool = False):
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🛒 Obunalar"),
        KeyboardButton(text="💎 Gemini nima?")
    )
    builder.row(
        KeyboardButton(text="📖 Yo'riqnoma"),
        KeyboardButton(text="⭐ Izohlar")
    )
    builder.row(
        KeyboardButton(text="👥 Referal"),
        KeyboardButton(text="📞 Yordam")
    )
    builder.row(
        KeyboardButton(text="👤 Kabinet")
    )
    if is_admin:
        builder.row(KeyboardButton(text="🛠 Admin Panel"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def cancel_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="❌ Bekor qilish"))
    return builder.as_markup(resize_keyboard=True)


def back_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="◀️ Orqaga"))
    return builder.as_markup(resize_keyboard=True)


def quantity_kb(max_qty: int = 10):
    builder = InlineKeyboardBuilder()
    buttons = []
    for i in range(1, min(max_qty, 10) + 1):
        buttons.append(InlineKeyboardButton(text=str(i), callback_data=f"qty:{i}"))
    # 2 rows of 5
    for i in range(0, len(buttons), 5):
        builder.row(*buttons[i:i+5])
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_order"))
    return builder.as_markup()


def subscriptions_kb(subs: list):
    builder = InlineKeyboardBuilder()
    for sub in subs:
        available = sub.get("available", 0) if isinstance(sub, dict) else 0
        name = sub["name"] if isinstance(sub, dict) else sub["name"]
        price = sub["price"] if isinstance(sub, dict) else sub["price"]
        sub_id = sub["id"] if isinstance(sub, dict) else sub["id"]
        text = f"{name} — {price:,} so'm"
        if available > 0:
            text += f" ({available} ta)"
        else:
            text += " (tugagan)"
        builder.row(InlineKeyboardButton(text=text, callback_data=f"sub:{sub_id}"))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_order"))
    return builder.as_markup()


def confirm_payment_kb(order_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ To'lov qildim", callback_data=f"paid:{order_id}"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_order")
    )
    return builder.as_markup()


def admin_confirm_kb(order_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"admin_confirm:{order_id}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"admin_reject:{order_id}")
    )
    return builder.as_markup()


def admin_panel_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📊 Statistika"),
        KeyboardButton(text="💳 Kartalar")
    )
    builder.row(
        KeyboardButton(text="📦 Obunalar boshqaruvi"),
        KeyboardButton(text="🔗 Linklar qo'shish")
    )
    builder.row(
        KeyboardButton(text="⚙️ Sozlamalar"),
        KeyboardButton(text="📢 Reklama")
    )
    builder.row(
        KeyboardButton(text="📋 Buyurtmalar"),
        KeyboardButton(text="👥 Foydalanuvchilar")
    )
    builder.row(KeyboardButton(text="◀️ Asosiy menyu"))
    return builder.as_markup(resize_keyboard=True)


def cards_manage_kb(cards: list):
    builder = InlineKeyboardBuilder()
    for card in cards:
        builder.row(
            InlineKeyboardButton(
                text=f"{card['card_number'][:6]}... | {card['card_owner']}",
                callback_data=f"card_view:{card['id']}"
            )
        )
    builder.row(InlineKeyboardButton(text="➕ Yangi karta qo'shish", callback_data="card_add"))
    builder.row(InlineKeyboardButton(text="◀️ Orqaga", callback_data="admin_back"))
    return builder.as_markup()


def card_actions_kb(card_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✏️ Raqamni o'zgartirish", callback_data=f"card_edit_num:{card_id}"),
        InlineKeyboardButton(text="👤 Egasi o'zgartirish", callback_data=f"card_edit_owner:{card_id}")
    )
    builder.row(InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"card_del:{card_id}"))
    builder.row(InlineKeyboardButton(text="◀️ Orqaga", callback_data="cards_list"))
    return builder.as_markup()


def subs_manage_kb(subs: list):
    builder = InlineKeyboardBuilder()
    for sub in subs:
        status = "✅" if sub["is_active"] else "❌"
        builder.row(
            InlineKeyboardButton(
                text=f"{status} {sub['name']} — {sub['price']:,}",
                callback_data=f"sub_manage:{sub['id']}"
            )
        )
    builder.row(InlineKeyboardButton(text="➕ Yangi obuna qo'shish", callback_data="sub_add"))
    builder.row(InlineKeyboardButton(text="◀️ Orqaga", callback_data="admin_back"))
    return builder.as_markup()


def sub_actions_kb(sub_id: int, is_active: bool):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✏️ Nom", callback_data=f"sub_edit_name:{sub_id}"),
        InlineKeyboardButton(text="💰 Narx", callback_data=f"sub_edit_price:{sub_id}")
    )
    builder.row(
        InlineKeyboardButton(text="📝 Tavsif", callback_data=f"sub_edit_desc:{sub_id}"),
        InlineKeyboardButton(text="🔢 Max miqdor", callback_data=f"sub_edit_max:{sub_id}")
    )
    toggle_text = "🔴 O'chirish" if is_active else "🟢 Yoqish"
    builder.row(InlineKeyboardButton(text=toggle_text, callback_data=f"sub_toggle:{sub_id}"))
    builder.row(InlineKeyboardButton(text="🔗 Linklar qo'shish", callback_data=f"sub_add_links:{sub_id}"))
    builder.row(InlineKeyboardButton(text="◀️ Orqaga", callback_data="subs_list"))
    return builder.as_markup()


def settings_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💎 Gemini ma'lumot", callback_data="set_gemini_info"))
    builder.row(InlineKeyboardButton(text="📖 Yo'riqnoma matni", callback_data="set_guide"))
    builder.row(InlineKeyboardButton(text="👋 Xush kelibsiz matni", callback_data="set_welcome"))
    builder.row(InlineKeyboardButton(text="👥 Referal matni", callback_data="set_referral_msg"))
    builder.row(InlineKeyboardButton(text="📞 Admin username", callback_data="set_admin_user"))
    builder.row(InlineKeyboardButton(text="📢 Majburiy kanal", callback_data="set_channel"))
    builder.row(InlineKeyboardButton(text="🔢 Referal chegarasi", callback_data="set_ref_threshold"))
    builder.row(InlineKeyboardButton(text="◀️ Orqaga", callback_data="admin_back"))
    return builder.as_markup()


def reviews_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✍️ Izoh yozish", callback_data="write_review"))
    builder.row(InlineKeyboardButton(text="📋 Barcha izohlar", callback_data="all_reviews"))
    return builder.as_markup()


def channel_check_kb(channel: str):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=f"https://t.me/{channel.replace('@', '')}"))
    builder.row(InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub"))
    return builder.as_markup()


def remove_kb():
    return ReplyKeyboardRemove()
