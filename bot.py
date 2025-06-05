import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from dotenv import load_dotenv

# .env faylini yuklash
load_dotenv()

# Logger sozlamasi
logging.basicConfig(level=logging.INFO)

# Muhitdan o‘qish
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))
GROUP_ID = int(os.getenv("GROUP_ID", "0"))

if not BOT_TOKEN or not ADMIN_IDS or not GROUP_ID:
    logging.error("❌ .env faylidagi maʼlumotlar toʻliq emas!")
    exit()

# Bot va dispatcher
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Holatlar
class OrderStates(StatesGroup):
    choosing_service = State()
    confirming_order = State()
    waiting_payment = State()

# Asosiy menyu tugmalari
main_menu_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_menu_kb.add(
    "🕋 Umra Paketlari", "🛂 Visa Xizmatlari",
    "🌙 Ravza Ruxsatnomalari", "🚗 Transport Xizmatlari",
    "🚆 Po‘ezd Biletlar", "✈️ Aviabiletlar",
    "🍽️ Guruh Ovqatlar"
)

# Orqaga/Bekor qilish
back_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
back_kb.add("🔙 Orqaga", "❌ Bekor qilish")

# To‘lov variantlari paneli
payment_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
payment_kb.add("💳 Uzcard", "💳 Humo", "💳 Visa", "🪙 Crypto", "🔙 Orqaga")

# Xizmatlar
services_info = {
    "umra_paket": {
        "name": "🕋 Umra Paketlari",
        "description": "✅ Oddiy Paket: $1100 dan\n✅ VIP Paket: $2000 dan\n\nPaketga kiradi:\n- Parvoz, mehmonxona, transport\n- Guruh ovqatlar\n- Qo‘llab-quvvatlash",
        "managers": ["@vip_arabiy", "@V001VB"]
    },
    "visa": {
        "name": "🛂 Visa Xizmatlari",
        "description": "🛂 Turist Visa: $120\n🕋 Umra Visa: $160\n\nVizangiz bo‘lsa, Ravza ruxsatnomasini alohida buyurtma qiling.",
        "managers": ["@vip_arabiy", "@V001VB"]
    },
    "ravza": {
        "name": "🌙 Ravza Ruxsatnomalari",
        "description": "🎟️ Vizasi bo‘lganlarga: 15 SAR\n🎟️ Vizasi bo‘lmaganlarga: 20 SAR\n\nGuruhlar uchun chegirmalar mavjud.",
        "managers": ["@vip_arabiy", "@V001VB"]
    },
    "transport": {
        "name": "🚗 Transport Xizmatlari",
        "description": "- Avtobus, taksi, VIP transport\nNarxlar bo‘yicha managerga murojaat qiling.",
        "managers": ["@vip_arabiy", "@V001VB"]
    },
    "train": {
        "name": "🚆 Po‘ezd Biletlar",
        "description": "• Madina – Makka\n• Makka – Madina\n• Riyadh – Dammam\n• Jeddah – Makka\n\nNarxlar yo‘nalish bo‘yicha farqlanadi.",
        "managers": ["@vip_arabiy", "@V001VB"]
    },
    "avia": {
        "name": "✈️ Aviabiletlar",
        "description": "Barcha yo‘nalishlarga chipta olish xizmati.\nNarxlar siz tanlagan yo‘nalishga bog‘liq.",
        "managers": ["@vip_arabiy", "@V001VB"]
    },
    "food": {
        "name": "🍽️ Guruh Ovqatlar",
        "description": "Guruhlar uchun milliy ovqatlar.\nNarxlar va menyu haqida manager bilan bog‘laning.",
        "managers": ["@vip_arabiy", "@V001VB"]
    },
}

# To‘lov ma'lumotlari
payment_details = {
    "Uzcard": "💳 *Uzcard*\n1. 8600 0304 9680 2624\n   Khamidov Ibodulloh\n2. 5614 6822 1222 3368\n   Khamidov Ibodulloh",
    "Humo": "💳 *Humo*\n9860 1001 2621 9243\nKhamidov Ibodulloh",
    "Visa": "💳 *Visa*\n1. 4140 8400 0184 8680\n   Khamidov Ibodulloh\n2. 4278 3100 2389 5840\n   Khamidov Ibodulloh",
    "Crypto": "🪙 *Crypto*\nUSDT (TRC20): `TLGiUsNzQ8n31x3VwsYiWEU97jdftTDqT3`\nETH (BEP20): `0xa11fb72cc1ee74cfdaadb25ab2530dd32bafa8f8`\nBTC (BEP20): `0xa11fb72cc1ee74cfdaadb25ab2530dd32bafa8f8`"
}

channels_text = "\n📢 Bizning kanallar:\n@umrajet\n@the_ravza"

# /start
@dp.message_handler(commands=["start", "help"])
async def cmd_start(message: types.Message):
    await message.answer(
        f"👋 Assalomu alaykum, {message.from_user.full_name}!\n\nXizmat turini tanlang:",
        reply_markup=main_menu_kb
    )

# Xizmat tanlash
@dp.message_handler(lambda msg: msg.text in [v["name"] for v in services_info.values()])
async def service_handler(message: types.Message, state: FSMContext):
    for key, value in services_info.items():
        if message.text == value["name"]:
            await state.update_data(service=key)
            text = f"{value['name']}\n\n{value['description']}\n\n👤 Managerlar: {', '.join(value['managers'])}"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("✅ Buyurtma berish", "🔙 Orqaga")
            await message.answer(text, reply_markup=kb)
            await OrderStates.choosing_service.set()
            return

# Buyurtmani tasdiqlash
@dp.message_handler(lambda msg: msg.text == "✅ Buyurtma berish", state=OrderStates.choosing_service)
async def confirm_handler(message: types.Message):
    await message.answer("To‘lov turini tanlang:", reply_markup=payment_kb)
    await OrderStates.confirming_order.set()

# To‘lov usuli tanlash
@dp.message_handler(lambda msg: msg.text.startswith("💳") or msg.text.startswith("🪙"), state=OrderStates.confirming_order)
async def pay_method_handler(message: types.Message):
    key = message.text.replace("💳 ", "").replace("🪙 ", "")
    info = payment_details.get(key, "Maʼlumot topilmadi")
    await message.answer(info + channels_text, reply_markup=back_kb)
    await OrderStates.waiting_payment.set()

# Kvitansiya yuborish
@dp.message_handler(content_types=types.ContentTypes.DOCUMENT, state=OrderStates.waiting_payment)
async def receive_payment_doc(message: types.Message, state: FSMContext):
    data = await state.get_data()
    service_key = data.get("service")
    service = services_info.get(service_key)

    notify = (
        f"📥 Yangi buyurtma!\n\n"
        f"👤 Foydalanuvchi: {message.from_user.full_name} (ID: {message.from_user.id})\n"
        f"🛎 Xizmat: {service['name']}\n"
        f"🧾 Kvitansiya: hujjat\n"
        f"👥 Managerlar: {', '.join(service['managers'])}"
    )

    for admin in ADMIN_IDS:
        try:
            await bot.send_message(admin, notify)
            await bot.send_document(admin, message.document.file_id)
        except Exception as e:
            logging.warning(f"Adminga yuborishda xatolik: {e}")

    await message.answer("✅ Buyurtmangiz qabul qilindi. Tez orada siz bilan managerlar bog‘lanadi.", reply_markup=main_menu_kb)
    await state.finish()

# Orqaga yoki bekor qilish
@dp.message_handler(lambda msg: msg.text in ["🔙 Orqaga", "❌ Bekor qilish"], state="*")
async def back_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("🏠 Asosiy menyu:", reply_markup=main_menu_kb)

# Boshqa xabarlar
@dp.message_handler()
async def unknown_handler(message: types.Message):
    await message.answer("Iltimos, menyudan foydalaning yoki /start buyrug‘ini bosing.", reply_markup=main_menu_kb)

# Ishga tushirish
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
