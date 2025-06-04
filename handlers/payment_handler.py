from aiogram import types
from aiogram.dispatcher import FSMContext
from config import bot, ADMIN_IDS, GROUP_ID
from states import OrderStates
from handlers.start_handler import services_info, format_managers, channels_text
import logging

# To‘lov uchun ma’lumot
@dp.message_handler(lambda m: m.text == "To‘lov uchun ma’lumot", state=OrderStates.confirming_order)
async def payment_info_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    service_key = data.get("service")
    info = services_info.get(service_key)

    text = (
        f"💳 {info['name']} uchun to‘lov usullari:\n\n"
        "1️⃣ Uzcard, Humo, Visa kartalari orqali to‘lov qilishingiz mumkin.\n"
        "2️⃣ Crypto pul o'tkazmalari qabul qilinadi.\n"
        "3️⃣ To‘lovni amalga oshirgach, kvitansiyani shu yerga yuboring.\n\n"
        f"{channels_text}"
    )
    await message.answer(text, reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🔙 Orqaga"))
    await OrderStates.waiting_payment.set()


# Kvitansiyani qabul qilish
@dp.message_handler(content_types=types.ContentTypes.DOCUMENT, state=OrderStates.waiting_payment)
async def receive_payment_receipt_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    service_key = data.get("service")
    info = services_info.get(service_key)

    order_text = (
        f"🆕 Yangi buyurtma!\n\n"
        f"👤 Foydalanuvchi: {message.from_user.full_name} (ID: {message.from_user.id})\n"
        f"🔧 Xizmat: {info['name']}\n"
        f"🧑‍💼 Managerlar: {format_managers(info['managers'])}\n\n"
        f"📎 To‘lov kvitansiyasi qabul qilindi.\n\n"
        f"📢 @vip_arabiy - asosiy manager\n"
        f"📢 @V001VB - zaxira manager\n\n"
        f"📣 Kanallar: @umrajet | @the_ravza"
    )

    # Adminlarga xabar yuborish
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, order_text)
            await bot.send_document(admin_id, message.document.file_id)
        except Exception as e:
            logging.error(f"Admin {admin_id}ga xabar yuborishda xato: {e}")

    # Guruhga yuborish
    try:
        await bot.send_message(GROUP_ID, order_text)
        await bot.send_document(GROUP_ID, message.document.file_id)
    except Exception as e:
        logging.error(f"Guruhga yuborishda xato: {e}")

    await message.answer(
        "✅ To‘lov kvitansiyasi qabul qilindi! Buyurtmangiz ko‘rib chiqiladi. Tez orada managerlar siz bilan bog‘lanadi.",
        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🔙 Asosiy menyu")
    )
    await state.finish()
