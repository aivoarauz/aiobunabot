from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.db import (
    add_user, get_user, get_setting, get_subscriptions, get_subscription,
    get_available_links_count, create_order, update_order, get_order,
    get_active_cards, add_review, get_reviews, get_referrals_count,
    get_stats, get_and_mark_links, add_earned
)
from keyboards.keyboards import (
    admin_confirm_kb,
    main_menu_kb, cancel_kb, quantity_kb, subscriptions_kb,
    confirm_payment_kb, reviews_kb, channel_check_kb, remove_kb
)
from utils.helpers import is_admin, check_channel_member, get_admin_username
from config import ADMIN_IDS

router = Router()


class OrderStates(StatesGroup):
    choosing_sub = State()
    choosing_qty = State()
    waiting_payment = State()
    waiting_check = State()


class ReviewStates(StatesGroup):
    writing = State()


async def ensure_subscribed(message: Message, bot: Bot) -> bool:
    channel = await get_setting("required_channel", "@aivora_uz")
    if not await check_channel_member(bot, message.from_user.id, channel):
        await message.answer(
            f"❗️ Botdan foydalanish uchun avval kanalimizga obuna bo'ling!\n\n"
            f"📢 Kanal: {channel}",
            reply_markup=channel_check_kb(channel)
        )
        return False
    return True


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    args = message.text.split()
    referrer_id = None
    if len(args) > 1 and args[1].startswith("ref"):
        try:
            referrer_id = int(args[1][3:])
        except ValueError:
            pass

    await add_user(
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.full_name or "",
        referrer_id
    )

    # Check referral threshold
    if referrer_id:
        count = await get_referrals_count(referrer_id)
        threshold = int(await get_setting("referral_threshold", "10"))
        if count >= threshold:
            admin_user = await get_admin_username()
            try:
                await bot.send_message(
                    referrer_id,
                    f"🎉 Tabriklaymiz! Siz botga {count} ta odam qo'shdingiz!\n"
                    f"Adminga yozing: @{admin_user}"
                )
            except Exception:
                pass
            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_message(
                        admin_id,
                        f"🎁 Foydalanuvchi {referrer_id} {count} ta referal to'pladi!"
                    )
                except Exception:
                    pass

    if not await ensure_subscribed(message, bot):
        return

    welcome = await get_setting("welcome_text", "Assalomu alaykum! 👋\nAIVORA obuna botiga xush kelibsiz!")
    await message.answer(
        welcome,
        reply_markup=main_menu_kb(is_admin(message.from_user.id))
    )


@router.callback_query(F.data == "check_sub")
async def check_subscription(callback: CallbackQuery, bot: Bot):
    channel = await get_setting("required_channel", "@aivora_uz")
    if await check_channel_member(bot, callback.from_user.id, channel):
        await callback.message.delete()
        welcome = await get_setting("welcome_text", "Assalomu alaykum!")
        await callback.message.answer(
            welcome + "\n\n✅ Obuna tasdiqlandi!",
            reply_markup=main_menu_kb(is_admin(callback.from_user.id))
        )
    else:
        await callback.answer("❌ Hali obuna bo'lmadingiz!", show_alert=True)


@router.message(F.text == "🛒 Obunalar")
async def show_subscriptions(message: Message, state: FSMContext, bot: Bot):
    if not await ensure_subscribed(message, bot):
        return
    await state.clear()
    subs = await get_subscriptions()
    if not subs:
        await message.answer("Hozircha obunalar yo'q.")
        return

    sub_list = []
    for sub in subs:
        available = await get_available_links_count(sub["id"])
        sub_list.append({
            "id": sub["id"],
            "name": sub["name"],
            "price": sub["price"],
            "available": available
        })

    text = "🛒 Mavjud obunalar:\n\n"
    for s in sub_list:
        text += f"• <b>{s['name']}</b> — {s['price']:,} so'm"
        if s["available"] > 0:
            text += f" | Qolgan: {s['available']} ta\n"
        else:
            text += " | <i>Tugagan</i>\n"

    await message.answer(text, reply_markup=subscriptions_kb(sub_list), parse_mode="HTML")
    await state.set_state(OrderStates.choosing_sub)


@router.callback_query(F.data.startswith("sub:"), OrderStates.choosing_sub)
async def choose_subscription(callback: CallbackQuery, state: FSMContext):
    sub_id = int(callback.data.split(":")[1])
    sub = await get_subscription(sub_id)
    if not sub or not sub["is_active"]:
        await callback.answer("Bu obuna mavjud emas!", show_alert=True)
        return

    available = await get_available_links_count(sub_id)
    if available == 0:
        admin_user = await get_admin_username()
        await callback.message.edit_text(
            f"❌ <b>{sub['name']}</b> uchun linklar tugagan.\n\n"
            f"Adminga yozing: @{admin_user}",
            parse_mode="HTML"
        )
        await state.clear()
        return

    max_qty = min(sub["max_quantity"], available, 10)
    await state.update_data(sub_id=sub_id, sub_name=sub["name"], price=sub["price"], max_qty=max_qty)
    await callback.message.edit_text(
        f"📦 <b>{sub['name']}</b>\n"
        f"💰 Narxi: <b>{sub['price']:,} so'm</b>\n"
        f"📝 {sub['description'] or ''}\n\n"
        f"Nechta olmoqchisiz? (1-{max_qty})",
        reply_markup=quantity_kb(max_qty),
        parse_mode="HTML"
    )
    await state.set_state(OrderStates.choosing_qty)


@router.callback_query(F.data.startswith("qty:"), OrderStates.choosing_qty)
async def choose_quantity(callback: CallbackQuery, state: FSMContext, bot: Bot):
    qty = int(callback.data.split(":")[1])
    data = await state.get_data()
    sub_id = data["sub_id"]
    price = data["price"]
    max_qty = data["max_qty"]

    if qty < 1 or qty > max_qty:
        await callback.answer("Noto'g'ri miqdor!", show_alert=True)
        return

    total = price * qty
    order_id = await create_order(callback.from_user.id, sub_id, qty, total)
    await state.update_data(order_id=order_id, quantity=qty, total=total)

    cards = await get_active_cards()
    card_text = ""
    if cards:
        for c in cards:
            card_text += f"💳 <code>{c['card_number']}</code>\n👤 {c['card_owner']}\n\n"
    else:
        card_text = "⚠️ Hozircha karta qo'shilmagan. Adminga murojaat qiling.\n\n"

    text = (
        f"✅ Buyurtma yaratildi!\n\n"
        f"📦 {data['sub_name']}\n"
        f"🔢 Miqdor: {qty} ta\n"
        f"💰 Jami: <b>{total:,} so'm</b>\n\n"
        f"⬇️ To'lov uchun kartalar:\n{card_text}"
        f"To'lovni amalga oshirib, «✅ To'lov qildim» tugmasini bosing."
    )
    await callback.message.edit_text(text, reply_markup=confirm_payment_kb(order_id), parse_mode="HTML")
    await state.set_state(OrderStates.waiting_payment)


@router.callback_query(F.data.startswith("paid:"), OrderStates.waiting_payment)
async def payment_done(callback: CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split(":")[1])
    await update_order(order_id, status="waiting_check")
    await callback.message.edit_text(
        "📸 Iltimos, to'lov cheki (skrinshot) rasmini yuboring.\n\n"
        "Rasim yuborilgach admin tekshiradi.",
        reply_markup=None
    )
    await callback.message.answer("❌ Bekor qilish uchun tugmani bosing:", reply_markup=cancel_kb())
    await state.set_state(OrderStates.waiting_check)
    await state.update_data(order_id=order_id)


@router.message(OrderStates.waiting_check, F.photo)
async def receive_check(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    order_id = data.get("order_id")
    if not order_id:
        await message.answer("Xatolik yuz berdi. Qaytadan boshlang.")
        await state.clear()
        return

    photo = message.photo[-1]
    await update_order(order_id, check_file_id=photo.file_id, status="waiting_check")

    order = await get_order(order_id)
    sub = await get_subscription(order["subscription_id"])

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_photo(
                admin_id,
                photo.file_id,
                caption=(
                    f"🧾 Yangi to'lov cheki!\n\n"
                    f"🆔 Buyurtma: #{order_id}\n"
                    f"👤 User: {message.from_user.id} (@{message.from_user.username or 'yoq'})\n"
                    f"📦 {sub['name'] if sub else '?'}\n"
                    f"🔢 Miqdor: {order['quantity']}\n"
                    f"💰 Summa: {order['total_price']:,} so'm"
                ),
                reply_markup=admin_confirm_kb(order_id)
            )
        except Exception as e:
            print(f"Admin notify error: {e}")

    await message.answer(
        "✅ Chek yuborildi! Admin tekshirmoqda. Kuting...",
        reply_markup=main_menu_kb(is_admin(message.from_user.id))
    )
    await state.clear()


@router.message(OrderStates.waiting_check)
async def waiting_check_wrong(message: Message):
    if message.text == "❌ Bekor qilish":
        return  # handled elsewhere
    await message.answer("📸 Iltimos, faqat chek rasmini yuboring yoki bekor qiling.")


@router.callback_query(F.data == "cancel_order")
async def cancel_order_cb(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("order_id")
    if order_id:
        await update_order(order_id, status="cancelled")
    await state.clear()
    await callback.message.edit_text("❌ Buyurtma bekor qilindi.")
    await callback.message.answer(
        "Asosiy menyu:",
        reply_markup=main_menu_kb(is_admin(callback.from_user.id))
    )


@router.message(F.text == "❌ Bekor qilish")
async def cancel_order_msg(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("order_id")
    if order_id:
        await update_order(order_id, status="cancelled")
    await state.clear()
    await message.answer(
        "❌ Amal bekor qilindi.",
        reply_markup=main_menu_kb(is_admin(message.from_user.id))
    )


@router.message(F.text == "💎 Gemini nima?")
async def gemini_info(message: Message, bot: Bot):
    if not await ensure_subscribed(message, bot):
        return
    info = await get_setting("gemini_info")
    await message.answer(info)


@router.message(F.text == "📖 Yo'riqnoma")
async def guide(message: Message, bot: Bot):
    if not await ensure_subscribed(message, bot):
        return
    text = await get_setting("guide_text")
    admin_user = await get_admin_username()
    text = text.replace("{admin}", admin_user)
    await message.answer(text)


@router.message(F.text == "📞 Yordam")
async def help_cmd(message: Message, bot: Bot):
    if not await ensure_subscribed(message, bot):
        return
    admin_user = await get_admin_username()
    await message.answer(
        f"📞 Yordam kerakmi?\n\n"
        f"Admin bilan bog'laning: @{admin_user}",
        reply_markup=main_menu_kb(is_admin(message.from_user.id))
    )


@router.message(F.text == "👥 Referal")
async def referral(message: Message, bot: Bot):
    if not await ensure_subscribed(message, bot):
        return
    count = await get_referrals_count(message.from_user.id)
    threshold = int(await get_setting("referral_threshold", "10"))
    bot_info = await bot.get_me()
    link = f"https://t.me/{bot_info.username}?start=ref{message.from_user.id}"
    await message.answer(
        f"👥 <b>Referal tizimi</b>\n\n"
        f"Sizning linkingiz:\n<code>{link}</code>\n\n"
        f"📊 Siz qo'shgan odamlar: <b>{count}</b> ta\n"
        f"🎯 Maqsad: {threshold} ta\n\n"
        f"{threshold} ta odam qo'shsangiz — maxsus sovg'a!",
        parse_mode="HTML"
    )


@router.message(F.text == "👤 Kabinet")
async def cabinet(message: Message, bot: Bot):
    if not await ensure_subscribed(message, bot):
        return
    user = await get_user(message.from_user.id)
    count = await get_referrals_count(message.from_user.id)
    await message.answer(
        f"👤 <b>Shaxsiy kabinet</b>\n\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n"
        f"👤 Ism: {message.from_user.full_name}\n"
        f"📎 Username: @{message.from_user.username or 'yoq'}\n"
        f"👥 Referallar: {count} ta\n"
        f"📅 Ro'yxatdan o'tgan: {user['joined_at'][:10] if user else '-'}",
        parse_mode="HTML"
    )


@router.message(F.text == "⭐ Izohlar")
async def reviews_menu(message: Message, bot: Bot):
    if not await ensure_subscribed(message, bot):
        return
    await message.answer(
        "⭐ Izohlar bo'limi\n\n"
        "Boshqalarning fikrlarini o'qing yoki o'zingiz izoh qoldiring!",
        reply_markup=reviews_kb()
    )


@router.callback_query(F.data == "write_review")
async def start_review(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "✍️ Izohingizni yozing (matn):\n\n"
        "❌ Bekor qilish uchun tugmani bosing.",
        reply_markup=cancel_kb()
    )
    await state.set_state(ReviewStates.writing)


@router.message(ReviewStates.writing)
async def save_review(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=main_menu_kb(is_admin(message.from_user.id)))
        return
    if not message.text or len(message.text) < 5:
        await message.answer("Izoh juda qisqa. Qayta yozing.")
        return
    await add_review(
        message.from_user.id,
        message.from_user.username or "",
        message.text
    )
    await state.clear()
    await message.answer(
        "✅ Izohingiz qabul qilindi! Rahmat 🙏",
        reply_markup=main_menu_kb(is_admin(message.from_user.id))
    )


@router.callback_query(F.data == "all_reviews")
async def show_reviews(callback: CallbackQuery):
    reviews = await get_reviews(15)
    if not reviews:
        await callback.message.answer("Hali izohlar yo'q.")
        return
    text = "⭐ <b>So'nggi izohlar:</b>\n\n"
    for r in reviews:
        uname = f"@{r['username']}" if r['username'] else f"ID:{r['user_id']}"
        text += f"👤 {uname}\n💬 {r['text']}\n📅 {r['created_at'][:10]}\n\n"
    await callback.message.answer(text, parse_mode="HTML")
