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

# Menyu tugmalar
main_menu_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
main_menu_kb.add(
    "🕋 Umra Paketlari", "🛂 Visa Xizmatlari",
    "🌙 Ravza Ruxsatnomalari", "🚗 Transport Xizmatlari",
    "🚆 Po‘ezd Biletlar", "✈️ Aviabiletlar",
    "🍽️ Guruh Ovqatlar"
)

back_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
back_kb.add("🔙 Orqaga", "❌ Bekor qilish")

cancel_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
cancel_kb.add("❌ Bekor qilish")

# Xizmatlar ma'lumotlari
services_info = {
    "umra_paket": {
        "name": "🕋 Umra Paketlari",
        "description": "✅ Oddiy Paket: $1100 dan\n✅ VIP Paket: $2000 dan\n\nPaketga kiradi:\n- Parvoz, mehmonxona, transport\n- Guruh ovqatlar\n- Qo‘llab-quvvatlash\n\nSifatli xizmat kafolatlanadi.",
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
        "description": "• Madina - Makka\n• Riyadh - Dammam\n\nNarxlar yo‘nalishga qarab farqlanadi.",
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

payment_text = (
    "💳 To‘lov usullari:\n\n"
    "🔘 <b>UZCARD</b>\n8600 0304 9680 2624\n5614 6822 1222 3368\n<b>Egasi:</b> Khamidov Ibodulloh\n\n"
    "🔘 <b>HUMO</b>\n9860 1001 2621 9243\n<b>Egasi:</b> Khamidov Ibodulloh\n\n"
    "🔘 <b>VISA</b>\n4140 8400 0184 8680\n4278 3100 2389 5840\n<b>Egasi:</b> Khamidov Ibodulloh\n\n"
    "🔘 <b>USDT (TRC20)</b>\nTLGiUsNzQ8n31x3VwsYiWEU97jdftTDqT3\n\n"
    "🔘 <b>ETH / BTC (BEP20)</b>\n0xa11fb72cc1ee74cfdaadb25ab2530dd32bafa8f8\n\n"
    "📎 To‘lovdan so‘ng kvitansiyani hujjat sifatida yuboring."
)

channels_text = (
    "📢 Rasmiy kanallar:\n@umrajet\n@the_ravza"
)

# Foydali funksiya
def format_managers(managers):
    return ", ".join(managers)

# /start
@dp.message_handler(commands=["start", "help"])
async def start_handler(message: types.Message):
    text = (
        f"👋 Assalomu alaykum, {message.from_user.full_name}!\n\n"
        "UmraJet Botga xush kelibsiz! Xizmat turini tanlang:"
    )
    await message.answer(text, reply_markup=main_menu_kb)

# Xizmat tanlash
@dp.message_handler(lambda msg: msg.text in [v["name"] for v in services_info.values()])
async def service_handler(message: types.Message, state: FSMContext):
    for key, value in services_info.items():
        if message.text == value["name"]:
            await state.update_data(service=key)
            desc = (
                f"{value['name']}:\n\n{value['description']}\n\n"
                f"Managerlar: {format_managers(value['managers'])}"
            )
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("✅ Buyurtma berish", "🔙 Orqaga")
            await message.answer(desc, reply_markup=kb)
            await OrderStates.choosing_service.set()
            return

# Buyurtmani tasdiqlash
@dp.message_handler(lambda msg: msg.text == "✅ Buyurtma berish", state=OrderStates.choosing_service)
async def confirm_handler(message: types.Message, state: FSMContext):
    await message.answer("Buyurtmani tasdiqlaysizmi?\nTo‘lov ma’lumotlarini olish uchun davom eting.", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("💳 To‘lov ma’lumotlari", "❌ Bekor qilish"))
    await OrderStates.confirming_order.set()

# To‘lov info
@dp.message_handler(lambda msg: msg.text == "💳 To‘lov ma’lumotlari", state=OrderStates.confirming_order)
async def payment_handler(message: types.Message):
    await message.answer(payment_text + "\n\n" + channels_text, reply_markup=back_kb, parse_mode="HTML")
    await OrderStates.waiting_payment.set()

# Kvitansiyani qabul qilish
@dp.message_handler(content_types=types.ContentTypes.DOCUMENT, state=OrderStates.waiting_payment)
async def document_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    key = data.get("service")
    info = services_info.get(key)
    order_msg = (
        f"📥 Yangi buyurtma!\n\n"
        f"👤 Foydalanuvchi: {message.from_user.full_name} (ID: {message.from_user.id})\n"
        f"🛎 Xizmat: {info['name']}\n"
        f"🧾 Kvitansiya yuborildi.\n"
        f"👥 Managerlar: {format_managers(info['managers'])}\n\n"
        f"🔗 @umrajet\n🔗 @the_ravza"
    )
    for admin in ADMIN_IDS:
        try:
            await bot.send_message(admin, order_msg)
            await bot.send_document(admin, message.document.file_id)
        except Exception as e:
            logging.warning(f"⚠️ Adminga yuborilmadi: {e}")

    await message.answer("✅ Buyurtmangiz qabul qilindi. Tez orada siz bilan managerlar bog‘lanadi.", reply_markup=main_menu_kb)
    await state.finish()

# Orqaga / bekor qilish
@dp.message_handler(lambda msg: msg.text in ["🔙 Orqaga", "❌ Bekor qilish"], state="*")
async def cancel_back_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("🏠 Asosiy menyu:", reply_markup=main_menu_kb)

# Nomaʼlum xabar
@dp.message_handler()
async def unknown_msg(message: types.Message):
    await message.answer("Iltimos, menyudan foydalaning yoki /start buyrug‘ini bosing.", reply_markup=main_menu_kb)

# Ishga tushirish
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
