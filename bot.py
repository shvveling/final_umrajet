import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from handlers import payment_handler  # BU MUHIM!


logging.basicConfig(level=logging.INFO)

# .env dan o'qish
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = os.getenv("ADMIN_IDS")  # "123456789,987654321"
GROUP_ID = os.getenv("GROUP_ID")

if not BOT_TOKEN or not ADMIN_IDS or not GROUP_ID:
    logging.error("Iltimos, .env faylini to'liq va to'g'ri to'ldiring!")
    exit()

ADMIN_IDS = list(map(int, ADMIN_IDS.split(',')))
GROUP_ID = int(GROUP_ID)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class OrderStates(StatesGroup):
    choosing_service = State()
    confirming_order = State()
    waiting_payment = State()

# Menyular
main_menu_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_menu_kb.add("🕋 Umra Paketlari")
main_menu_kb.add("🛂 Visa Xizmatlari")
main_menu_kb.add("🌙 Ravza Ruxsatnomalari")
main_menu_kb.add("🚗 Transport Xizmatlari")
main_menu_kb.add("🚆 Po‘ezd Biletlar")
main_menu_kb.add("✈️ Aviabiletlar")
main_menu_kb.add("🍽️ Guruh Ovqatlar")

cancel_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
cancel_kb.add("❌ Bekor qilish")

back_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
back_kb.add("🔙 Orqaga")
back_kb.add("❌ Bekor qilish")

# Xizmatlar ma'lumotlari va narxlar
services_info = {
    "umra_paket": {
        "name": "🕋 Umra Paketlari",
        "description": (
            "Umra safaringiz uchun mukammal paketlar:\n\n"
            "✅ Oddiy Paket: $1100 dan\n"
            "✅ VIP Paket: $2000 dan\n\n"
            "Paketga kiradi:\n"
            "- Parvoz va mehmonxona\n"
            "- Transport xizmatlari\n"
            "- Guruh ovqatlar\n"
            "- Tasarruf va qo‘llab-quvvatlash\n\n"
            "Sifatli va qulay xizmatlar siz uchun."
        ),
        "managers": ["@vip_arabiy", "@V001VB"],
    },
    "visa": {
        "name": "🛂 Visa Xizmatlari",
        "description": (
            "Visa xizmatlari:\n\n"
            "🛂 Turist Visa: $120 dona uchun\n"
            "🕋 Umra Visa: $160 dona uchun\n\n"
            "Eslatma: Vizangiz bo‘lsa, Ravza ruxsatnomasi uchun murojaat qiling."
        ),
        "managers": ["@vip_arabiy", "@V001VB"],
    },
    "ravza": {
        "name": "🌙 Ravza Ruxsatnomalari",
        "description": (
            "Rawda ruxsatnomalari:\n\n"
            "🎟️ Vizasi bo‘lganlarga: 15 SAR/dona\n"
            "🎟️ Vizasi bo‘lmaganlarga: 20 SAR/dona\n\n"
            "Guruhlarga maxsus chegirmalar mavjud."
        ),
        "managers": ["@vip_arabiy", "@V001VB"],
    },
    "transport": {
        "name": "🚗 Transport Xizmatlari",
        "description": (
            "Transport xizmatlari:\n\n"
            "- Avtobus, Taksi, Shaxsiy transport\n"
            "Narxlar va batafsil ma'lumot uchun murojaat qiling."
        ),
        "managers": ["@vip_arabiy", "@V001VB"],
    },
    "train": {
        "name": "🚆 Po‘ezd Biletlar",
        "description": (
            "Po‘ezd yo‘nalishlari:\n\n"
            "• Madina - Makka\n"
            "• Madina - Riyadh\n"
            "• Riyadh - Dammam\n\n"
            "Narxlar yo‘nalishga qarab o‘zgaradi.\n"
            "Batafsil ma'lumot uchun murojaat qiling."
        ),
        "managers": ["@vip_arabiy", "@V001VB"],
    },
    "avia": {
        "name": "✈️ Aviabiletlar",
        "description": (
            "Dunyo bo‘ylab aviachipta xizmati.\n"
            "Yo‘nalish va narx mijoz talabiga qarab belgilanadi.\n"
            "Mutaxassislarimiz sizga yordam beradi."
        ),
        "managers": ["@vip_arabiy", "@V001VB"],
    },
    "food": {
        "name": "🍽️ Guruh Ovqatlar",
        "description": (
            "Katta guruhlar uchun maxsus ovqat xizmatlari.\n"
            "Turli milliy taomlar, sifatli xizmat.\n"
            "Narx va menyu haqida ma’lumot uchun murojaat qiling."
        ),
        "managers": ["@vip_arabiy", "@V001VB"],
    },
}

# To'lovlar bo'yicha ma'lumot
payment_methods_text = (
    "To‘lov usullari:\n"
    "💳 Uzcard, Humo, Visa kartalari orqali to‘lov\n"
    "🪙 Crypto pul o'tkazmalari\n"
    "🤝 Managerlar orqali naqd to‘lov\n\n"
    "To‘lovni amalga oshirganingizdan so‘ng, kvitansiyani yuboring."
)

channels_text = (
    "Rasmiy kanallarimiz:\n"
    "🔹 @umrajet\n"
    "🔹 @the_ravza\n"
)

def format_managers(managers_list):
    return ", ".join(managers_list)

# --- Handlerlar ---

@dp.message_handler(commands=["start", "help"])
async def cmd_start(message: types.Message):
    text = (
        f"Assalomu alaykum, {message.from_user.full_name}!\n\n"
        "UmraJet Botga xush kelibsiz! 🌟\n\n"
        "Quyidagi xizmatlardan birini tanlang:\n"
    )
    for key in services_info:
        text += f"\n{services_info[key]['name']}"
    text += f"\n\n{channels_text}"
    await message.answer(text, reply_markup=main_menu_kb)


@dp.message_handler(lambda m: m.text in [info["name"] for info in services_info.values()])
async def service_info_handler(message: types.Message, state: FSMContext):
    chosen_key = None
    for key, val in services_info.items():
        if message.text == val["name"]:
            chosen_key = key
            break

    if not chosen_key:
        await message.answer("Kechirasiz, bunday xizmat mavjud emas.", reply_markup=main_menu_kb)
        return

    info = services_info[chosen_key]
    text = (
        f"📌 {info['name']} haqida ma’lumot:\n\n"
        f"{info['description']}\n\n"
        f"{payment_methods_text}\n\n"
        f"Asosiy menejerlar: {format_managers(info['managers'])}\n\n"
        "Buyurtma berish uchun pastdagi tugmani bosing."
    )
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("✅ Buyurtma berish")
    kb.add("🔙 Orqaga")
    await message.answer(text, reply_markup=kb)
    await OrderStates.choosing_service.set()
    await state.update_data(service=chosen_key)


@dp.message_handler(lambda m: m.text == "🔙 Orqaga", state='*')
async def go_back_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Asosiy menyu:", reply_markup=main_menu_kb)


@dp.message_handler(lambda m: m.text == "❌ Bekor qilish", state='*')
async def cancel_order_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Buyurtma bekor qilindi. Asosiy menyu:", reply_markup=main_menu_kb)


@dp.message_handler(lambda m: m.text == "✅ Buyurtma berish", state=OrderStates.choosing_service)
async def confirm_order_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    service_key = data.get("service")

    if not service_key:
        await message.answer("Xizmat tanlanmadi. Iltimos, qayta tanlang.", reply_markup=main_menu_kb)
        await state.finish()
        return

    info = services_info[service_key]

    text = (
        f"Siz tanlagan xizmat: {info['name']}\n\n"
        "Buyurtmani tasdiqlaysizmi?\n"
        "Iltimos, to‘lovni amalga oshiring va kvitansiyani yuboring."
    )
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("To‘lov uchun ma’lumot")
    kb.add("❌ Bekor qilish")

    await message.answer(text, reply_markup=kb)
    await OrderStates.confirming_order.set()


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
    await message.answer(text, reply_markup=back_kb)
    await OrderStates.waiting_payment.set()


@dp.message_handler(content_types=types.ContentTypes.DOCUMENT, state=OrderStates.waiting_payment)
async def receive_payment_receipt_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    service_key = data.get("service")
    info = services_info.get(service_key)

    order_text = (
        f"🆕 Yangi buyurtma!\n\n"
        f"Foydalanuvchi: {message.from_user.full_name} (ID: {message.from_user.id})\n"
        f"Xizmat: {info['name']}\n"
        f"Managerlar: {format_managers(info['managers'])}\n\n"
        f"To‘lov kvitansiyasi qabul qilindi va tekshirilmoqda.\n\n"
        f"@{info['managers'][0]} - asosiy manager\n"
        f"@{info['managers'][1]} - zaxira manager\n\n"
        f"Rasmiy kanallar: @umrajet, @the_ravza"
    )

    # Managerlarga xabar yuborish
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, order_text)
            await bot.send_document(admin_id, message.document.file_id)
        except Exception as e:
            logging.error(f"Managerga xabar yuborishda xato: {e}")

    await message.answer(
        "To‘lov kvitansiyasi qabul qilindi! Buyurtmangiz ko‘rib chiqiladi. Tez orada managerlar siz bilan bog‘lanadi.",
        reply_markup=main_menu_kb
    )
    await state.finish()


@dp.message_handler()
async def fallback_handler(message: types.Message):
    await message.answer(
        "Iltimos, quyidagi menyudan birini tanlang yoki /start ni bosing.",
        reply_markup=main_menu_kb
    )

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
