from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from database.db import (
    get_stats, get_all_users_count, get_active_cards, add_card, update_card, delete_card,
    get_subscriptions, get_subscription, add_subscription, update_subscription,
    add_subscription_links, get_available_links_count, get_setting, set_setting,
    get_pending_orders, get_order, update_order, get_and_mark_links, add_earned,
    get_users_list
)
from keyboards.keyboards import (
    admin_panel_kb, main_menu_kb, cancel_kb, cards_manage_kb, card_actions_kb,
    subs_manage_kb, sub_actions_kb, settings_kb, admin_confirm_kb
)
from utils.helpers import is_admin, get_admin_username
from config import ADMIN_IDS

router = Router()


class AdminStates(StatesGroup):
    add_card_number = State()
    add_card_owner = State()
    edit_card_number = State()
    edit_card_owner = State()
    add_sub_name = State()
    add_sub_price = State()
    add_sub_desc = State()
    add_sub_max = State()
    edit_sub_name = State()
    edit_sub_price = State()
    edit_sub_desc = State()
    edit_sub_max = State()
    add_links = State()
    set_setting_value = State()
    broadcast = State()


def admin_only(func):
    async def wrapper(event, *args, **kwargs):
        user_id = event.from_user.id
        if not is_admin(user_id):
            if hasattr(event, "answer"):
                await event.answer("⛔ Ruxsat yo'q!", show_alert=True)
            return
        return await func(event, *args, **kwargs)
    return wrapper


@router.message(F.text == "🛠 Admin Panel")
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("🛠 Admin Panel", reply_markup=admin_panel_kb())


@router.message(F.text == "◀️ Asosiy menyu")
async def back_main(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyu:", reply_markup=main_menu_kb(is_admin(message.from_user.id)))


@router.message(F.text == "📊 Statistika")
async def stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    s = await get_stats()
    users = await get_all_users_count()
    subs = await get_subscriptions(active_only=False)
    pending = await get_pending_orders()
    
    text = (
        f"📊 <b>STATISTIKA</b>\n\n"
        f"💰 Jami ishlab topilgan: <b>{s['total_earned']:,} so'm</b>\n"
        f"📦 Jami buyurtmalar: {s['total_orders']}\n"
        f"👥 Jami foydalanuvchilar: {users}\n"
        f"⏳ Kutilayotgan buyurtmalar: {len(pending)}\n\n"
        f"📦 Obunalar:\n"
    )
    for sub in subs:
        avail = await get_available_links_count(sub["id"])
        text += f"• {sub['name']}: {avail} ta link qolgan\n"
    
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "💳 Kartalar")
async def cards_menu(message: Message):
    if not is_admin(message.from_user.id):
        return
    cards = await get_active_cards()
    if not cards:
        await message.answer(
            "Hozircha kartalar yo'q.\n➕ Qo'shish uchun tugmani bosing.",
            reply_markup=cards_manage_kb([])
        )
    else:
        await message.answer("💳 Faol kartalar:", reply_markup=cards_manage_kb(cards))


@router.callback_query(F.data == "cards_list")
async def cards_list_cb(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    cards = await get_active_cards()
    await callback.message.edit_text("💳 Faol kartalar:", reply_markup=cards_manage_kb(cards))


@router.callback_query(F.data == "card_add")
async def card_add_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.answer("💳 Karta raqamini kiriting:", reply_markup=cancel_kb())
    await state.set_state(AdminStates.add_card_number)


@router.message(AdminStates.add_card_number)
async def card_add_number(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_panel_kb())
        return
    await state.update_data(card_number=message.text.strip())
    await message.answer("👤 Karta egasining ismini kiriting:")
    await state.set_state(AdminStates.add_card_owner)


@router.message(AdminStates.add_card_owner)
async def card_add_owner(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_panel_kb())
        return
    data = await state.get_data()
    await add_card(data["card_number"], message.text.strip())
    await state.clear()
    await message.answer("✅ Karta qo'shildi!", reply_markup=admin_panel_kb())


@router.callback_query(F.data.startswith("card_view:"))
async def card_view(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    card_id = int(callback.data.split(":")[1])
    cards = await get_active_cards()
    card = next((c for c in cards if c["id"] == card_id), None)
    if not card:
        await callback.answer("Topilmadi")
        return
    await callback.message.edit_text(
        f"💳 <code>{card['card_number']}</code>\n👤 {card['card_owner']}",
        reply_markup=card_actions_kb(card_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("card_edit_num:"))
async def card_edit_num(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    card_id = int(callback.data.split(":")[1])
    await state.update_data(card_id=card_id)
    await callback.message.answer("Yangi karta raqamini kiriting:", reply_markup=cancel_kb())
    await state.set_state(AdminStates.edit_card_number)


@router.message(AdminStates.edit_card_number)
async def card_edit_num_save(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor.", reply_markup=admin_panel_kb())
        return
    data = await state.get_data()
    await update_card(data["card_id"], card_number=message.text.strip())
    await state.clear()
    await message.answer("✅ Yangilandi!", reply_markup=admin_panel_kb())


@router.callback_query(F.data.startswith("card_edit_owner:"))
async def card_edit_owner(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    card_id = int(callback.data.split(":")[1])
    await state.update_data(card_id=card_id)
    await callback.message.answer("Yangi egasini kiriting:", reply_markup=cancel_kb())
    await state.set_state(AdminStates.edit_card_owner)


@router.message(AdminStates.edit_card_owner)
async def card_edit_owner_save(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor.", reply_markup=admin_panel_kb())
        return
    data = await state.get_data()
    await update_card(data["card_id"], card_owner=message.text.strip())
    await state.clear()
    await message.answer("✅ Yangilandi!", reply_markup=admin_panel_kb())


@router.callback_query(F.data.startswith("card_del:"))
async def card_delete(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    card_id = int(callback.data.split(":")[1])
    await delete_card(card_id)
    await callback.answer("O'chirildi!")
    cards = await get_active_cards()
    await callback.message.edit_text("💳 Faol kartalar:", reply_markup=cards_manage_kb(cards))


@router.message(F.text == "📦 Obunalar boshqaruvi")
async def subs_manage(message: Message):
    if not is_admin(message.from_user.id):
        return
    subs = await get_subscriptions(active_only=False)
    await message.answer("📦 Obunalar:", reply_markup=subs_manage_kb(subs))


@router.callback_query(F.data == "subs_list")
async def subs_list_cb(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    subs = await get_subscriptions(active_only=False)
    await callback.message.edit_text("📦 Obunalar:", reply_markup=subs_manage_kb(subs))


@router.callback_query(F.data == "sub_add")
async def sub_add_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.answer("📦 Obuna nomini kiriting:", reply_markup=cancel_kb())
    await state.set_state(AdminStates.add_sub_name)


@router.message(AdminStates.add_sub_name)
async def sub_add_name(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor.", reply_markup=admin_panel_kb())
        return
    await state.update_data(name=message.text.strip())
    await message.answer("💰 Narxini kiriting (faqat raqam, so'mda):")
    await state.set_state(AdminStates.add_sub_price)


@router.message(AdminStates.add_sub_price)
async def sub_add_price(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor.", reply_markup=admin_panel_kb())
        return
    try:
        price = int(message.text.strip().replace(" ", "").replace(",", ""))
    except ValueError:
        await message.answer("Faqat raqam kiriting!")
        return
    await state.update_data(price=price)
    await message.answer("📝 Tavsifini kiriting:")
    await state.set_state(AdminStates.add_sub_desc)


@router.message(AdminStates.add_sub_desc)
async def sub_add_desc(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor.", reply_markup=admin_panel_kb())
        return
    await state.update_data(description=message.text.strip())
    await message.answer("🔢 Maksimal miqdorni kiriting (1-10):")
    await state.set_state(AdminStates.add_sub_max)


@router.message(AdminStates.add_sub_max)
async def sub_add_max(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor.", reply_markup=admin_panel_kb())
        return
    try:
        max_q = int(message.text.strip())
        if max_q < 1 or max_q > 50:
            raise ValueError
    except ValueError:
        await message.answer("1 dan 50 gacha raqam kiriting!")
        return
    data = await state.get_data()
    sub_id = await add_subscription(data["name"], data["price"], data["description"], max_q)
    await state.clear()
    await message.answer(
        f"✅ Obuna qo'shildi! ID: {sub_id}\n"
        f"Endi «🔗 Linklar qo'shish» orqali linklar qo'shing.",
        reply_markup=admin_panel_kb()
    )


@router.callback_query(F.data.startswith("sub_manage:"))
async def sub_manage(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    sub_id = int(callback.data.split(":")[1])
    sub = await get_subscription(sub_id)
    if not sub:
        await callback.answer("Topilmadi")
        return
    avail = await get_available_links_count(sub_id)
    await callback.message.edit_text(
       f"<b>{sub['name']}</b>\n"
        f"💰 {sub['price']:,} so'm\n"
        f"📝 {sub['description'] or '-'}\n"
        f"📦 Max: {sub['max_quantity']}\n"
        f"🔗 Qolgan linklar: {avail}\n"
        f"Holat: {'✅ Faol' if sub['is_active'] else '❌ Oʻchirilgan'}",
        reply_markup=sub_actions_kb(sub_id, bool(sub["is_active"])),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("sub_edit_name:"))
async def sub_edit_name(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.update_data(sub_id=int(callback.data.split(":")[1]))
    await callback.message.answer("Yangi nom:", reply_markup=cancel_kb())
    await state.set_state(AdminStates.edit_sub_name)


@router.message(AdminStates.edit_sub_name)
async def sub_edit_name_save(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor.", reply_markup=admin_panel_kb())
        return
    data = await state.get_data()
    await update_subscription(data["sub_id"], name=message.text.strip())
    await state.clear()
    await message.answer("✅ Yangilandi!", reply_markup=admin_panel_kb())


@router.callback_query(F.data.startswith("sub_edit_price:"))
async def sub_edit_price(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.update_data(sub_id=int(callback.data.split(":")[1]))
    await callback.message.answer("Yangi narx (raqam):", reply_markup=cancel_kb())
    await state.set_state(AdminStates.edit_sub_price)


@router.message(AdminStates.edit_sub_price)
async def sub_edit_price_save(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor.", reply_markup=admin_panel_kb())
        return
    try:
        price = int(message.text.strip().replace(" ", "").replace(",", ""))
    except ValueError:
        await message.answer("Raqam kiriting!")
        return
    data = await state.get_data()
    await update_subscription(data["sub_id"], price=price)
    await state.clear()
    await message.answer("✅ Yangilandi!", reply_markup=admin_panel_kb())


@router.callback_query(F.data.startswith("sub_edit_desc:"))
async def sub_edit_desc(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.update_data(sub_id=int(callback.data.split(":")[1]))
    await callback.message.answer("Yangi tavsif:", reply_markup=cancel_kb())
    await state.set_state(AdminStates.edit_sub_desc)


@router.message(AdminStates.edit_sub_desc)
async def sub_edit_desc_save(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor.", reply_markup=admin_panel_kb())
        return
    data = await state.get_data()
    await update_subscription(data["sub_id"], description=message.text.strip())
    await state.clear()
    await message.answer("✅ Yangilandi!", reply_markup=admin_panel_kb())


@router.callback_query(F.data.startswith("sub_edit_max:"))
async def sub_edit_max(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.update_data(sub_id=int(callback.data.split(":")[1]))
    await callback.message.answer("Yangi max miqdor:", reply_markup=cancel_kb())
    await state.set_state(AdminStates.edit_sub_max)


@router.message(AdminStates.edit_sub_max)
async def sub_edit_max_save(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor.", reply_markup=admin_panel_kb())
        return
    try:
        max_q = int(message.text.strip())
    except ValueError:
        await message.answer("Raqam kiriting!")
        return
    data = await state.get_data()
    await update_subscription(data["sub_id"], max_quantity=max_q)
    await state.clear()
    await message.answer("✅ Yangilandi!", reply_markup=admin_panel_kb())


@router.callback_query(F.data.startswith("sub_toggle:"))
async def sub_toggle(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    sub_id = int(callback.data.split(":")[1])
    sub = await get_subscription(sub_id)
    new_status = 0 if sub["is_active"] else 1
    await update_subscription(sub_id, is_active=new_status)
    await callback.answer("Holat o'zgardi!")
    sub = await get_subscription(sub_id)
    avail = await get_available_links_count(sub_id)
    await callback.message.edit_text(
        f"<b>{sub['name']}</b>\n"
        f"💰 {sub['price']:,} so'm\n"
        f"📝 {sub['description'] or '-'}\n"
        f"📦 Max: {sub['max_quantity']}\n"
        f"🔗 Qolgan linklar: {avail}\n"
        f"Holat: {'✅ Faol' if sub['is_active'] else '❌ Oʻchirilgan'}",
        reply_markup=sub_actions_kb(sub_id, bool(sub["is_active"])),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("sub_add_links:"))
async def sub_add_links_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    sub_id = int(callback.data.split(":")[1])
    await state.update_data(sub_id=sub_id)
    await callback.message.answer(
        "🔗 Linklarni yuboring (har birini yangi qatordan yoki vergul bilan):\n\n"
        "Masalan:",
        reply_markup=cancel_kb()
    )
    await state.set_state(AdminStates.add_links)


@router.message(F.text == "🔗 Linklar qo'shish")
async def links_add_menu(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    subs = await get_subscriptions(active_only=False)
    if not subs:
        await message.answer("Avval obuna qo'shing!")
        return
    text = "Qaysi obunaga link qo'shmoqchisiz? ID ni yuboring:\n\n"
    for s in subs:
        avail = await get_available_links_count(s["id"])
        text += f"ID {s['id']}: {s['name']} (qolgan: {avail})\n"
    await message.answer(text, reply_markup=cancel_kb())
    await state.set_state(AdminStates.add_links)
    await state.update_data(waiting_sub_id=True)


@router.message(AdminStates.add_links)
async def add_links_save(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor.", reply_markup=admin_panel_kb())
        return
    
    data = await state.get_data()
    if data.get("waiting_sub_id"):
        try:
            sub_id = int(message.text.strip())
            sub = await get_subscription(sub_id)
            if not sub:
                await message.answer("Bunday ID topilmadi!")
                return
            await state.update_data(sub_id=sub_id, waiting_sub_id=False)
            await message.answer("Endi linklarni yuboring (har biri yangi qatordan):")
            return
        except ValueError:
            await message.answer("Faqat raqam (ID) kiriting!")
            return
    
    sub_id = data.get("sub_id")
    if not sub_id:
        await message.answer("Xatolik. Qaytadan boshlang.")
        await state.clear()
        return
    
    raw = message.text.replace(",", "\n")
    links = [l.strip() for l in raw.split("\n") if l.strip()]
    if not links:
        await message.answer("Hech qanday to'g'ri link topilmadi. Qayta yuboring.")
        return
    
    await add_subscription_links(sub_id, links)
    await state.clear()
    await message.answer(f"✅ {len(links)} ta link qo'shildi!", reply_markup=admin_panel_kb())


@router.message(F.text == "⚙️ Sozlamalar")
async def settings_menu(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("⚙️ Sozlamalar:", reply_markup=settings_kb())


@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🛠 Admin Panelga qayting (tugmadan).")


@router.callback_query(F.data.startswith("set_"))
async def set_setting_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    key_map = {
        "set_gemini_info": ("gemini_info", "Gemini ma'lumot matnini yuboring:"),
        "set_guide": ("guide_text", "Yo'riqnoma matnini yuboring:"),
        "set_welcome": ("welcome_text", "Xush kelibsiz matnini yuboring:"),
        "set_referral_msg": ("referral_message", "Referal xabarini yuboring:"),
        "set_admin_user": ("admin_username", "Admin username (@siz):"),
        "set_channel": ("required_channel", "Majburiy kanal (@kanal):"),
        "set_ref_threshold": ("referral_threshold", "Referal chegarasi (raqam):"),
    }
    if callback.data not in key_map:
        return
    key, prompt = key_map[callback.data]
    await state.update_data(setting_key=key)
    await callback.message.answer(prompt, reply_markup=cancel_kb())
    await state.set_state(AdminStates.set_setting_value)


@router.message(AdminStates.set_setting_value)
async def set_setting_save(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor.", reply_markup=admin_panel_kb())
        return
    data = await state.get_data()
    key = data["setting_key"]
    value = message.text.strip()
    if key == "admin_username":
        value = value.replace("@", "")
    await set_setting(key, value)
    await state.clear()
    await message.answer("✅ Saqlandi!", reply_markup=admin_panel_kb())


@router.message(F.text == "📢 Reklama")
async def broadcast_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "📢 Reklama xabarini yuboring (matn yoki rasm+caption):\n"
        "Barcha foydalanuvchilarga yuboriladi.",
        reply_markup=cancel_kb()
    )
    await state.set_state(AdminStates.broadcast)


@router.message(AdminStates.broadcast)
async def broadcast_send(message: Message, state: FSMContext, bot: Bot):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor.", reply_markup=admin_panel_kb())
        return
    
    users = await get_users_list(5000)
    success = 0
    fail = 0
    await message.answer(f"⏳ {len(users)} ta foydalanuvchiga yuborilmoqda...")
    
    for u in users:
        try:
            if message.photo:
                await bot.send_photo(u["user_id"], message.photo[-1].file_id, caption=message.caption or "")
            else:
                await bot.send_message(u["user_id"], message.text or message.caption or "")
            success += 1
        except Exception:
            fail += 1
    
    await state.clear()
    await message.answer(
        f"✅ Yuborildi: {success}\n❌ Xato: {fail}",
        reply_markup=admin_panel_kb()
    )


@router.message(F.text == "📋 Buyurtmalar")
async def pending_orders(message: Message):
    if not is_admin(message.from_user.id):
        return
    orders = await get_pending_orders()
    if not orders:
        await message.answer("Kutilayotgan buyurtmalar yo'q.")
        return
    text = "⏳ Kutilayotgan buyurtmalar:\n\n"
    for o in orders[:20]:
        text += f"#{o['id']} | User:{o['user_id']} | {o['total_price']:,} so'm | {o['status']}\n"
    await message.answer(text)


@router.message(F.text == "👥 Foydalanuvchilar")
async def users_list(message: Message):
    if not is_admin(message.from_user.id):
        return
    count = await get_all_users_count()
    await message.answer(f"👥 Jami foydalanuvchilar: <b>{count}</b>", parse_mode="HTML")


# Admin confirm/reject order
@router.callback_query(F.data.startswith("admin_confirm:"))
async def admin_confirm_order(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q")
        return
    order_id = int(callback.data.split(":")[1])
    order = await get_order(order_id)
    if not order or order["status"] not in ("pending", "waiting_check"):
        await callback.answer("Buyurtma topilmadi yoki allaqachon qayta ishlangan", show_alert=True)
        return
    
    links = await get_and_mark_links(order["subscription_id"], order["quantity"], order["user_id"])
    if not links:
        await callback.answer("Yetarli link yo'q!", show_alert=True)
        admin_user = await get_admin_username()
        try:
            await bot.send_message(
                order["user_id"],
                f"❌ Afsuski, hozircha linklar tugagan.\nAdminga yozing: @{admin_user}"
            )
        except Exception:
            pass
        return
    
    links_text = "\n".join(links)
    await update_order(
        order_id,
        status="confirmed",
        links_sent=links_text,
        confirmed_at=datetime.now().isoformat(),
        admin_id=callback.from_user.id
    )
    await add_earned(order["total_price"])
    
    sub = await get_subscription(order["subscription_id"])
    try:
        await bot.send_message(
            order["user_id"],
            f"✅ <b>To'lovingiz tasdiqlandi!</b>\n\n"
            f"📦 {sub['name'] if sub else 'Obuna'}\n"
            f"🔢 Miqdor: {order['quantity']}\n\n"
            f"🔗 Sizning linkingiz(lar):\n{links_text}\n\n"
            f"Rahmat! Foydalaning 🚀",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Send link error: {e}")
    
    await callback.message.edit_caption(
        callback.message.caption + "\n\n✅ TASDIQLANDI",
        reply_markup=None
    )
    await callback.answer("Tasdiqlandi va link yuborildi!")


@router.callback_query(F.data.startswith("admin_reject:"))
async def admin_reject_order(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q")
        return
    order_id = int(callback.data.split(":")[1])
    order = await get_order(order_id)
    if not order:
        await callback.answer("Topilmadi")
        return
    
    await update_order(order_id, status="rejected", admin_id=callback.from_user.id)
    try:
        await bot.send_message(
            order["user_id"],
            "❌ To'lovingiz rad etildi.\n\n"
            "Sababini bilish uchun adminga yozing."
        )
    except Exception:
        pass
    
    await callback.message.edit_caption(
        callback.message.caption + "\n\n❌ RAD ETILDI",
        reply_markup=None
    )
    await callback.answer("Rad etildi")
