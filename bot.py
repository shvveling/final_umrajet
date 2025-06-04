import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# --- Sozlamalar ---
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = os.getenv("ADMIN_IDS")
GROUP_ID = os.getenv("GROUP_ID")

if not BOT_TOKEN or not ADMIN_IDS or not GROUP_ID:
    logging.error("⚠️ .env fayl to‘liq emas!")
    exit()

ADMIN_IDS = list(map(int, ADMIN_IDS.split(',')))
GROUP_ID = int(GROUP_ID)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# --- Holatlar ---
class OrderStates(StatesGroup):
    choosing_service = State()
    confirming_order = State()

# --- Menyu ---
main_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.row("🕋 Umra Paketlari", "🛂 Visa Xizmatlari")
main_menu.row("🌙 Ravza Ruxsatnomalari", "🚗 Transport Xizmatlari")
main_menu.row("🚆 Po‘ezd Biletlar", "✈️ Aviabiletlar")
main_menu.row("🍽️ Guruh Ovqatlar")

# --- Xizmatlar ---
services = {
    "🕋 Umra Paketlari": (
        "📿 Umra Paketlari\n"
        "✅ Oddiy: $1100+\n"
        "✅ VIP: $2000+\n"
        "- Parvoz, Mehmonxona, Transport, Ovqat, Ruxsatnomalar.\n\n"
        "Sifatli va qulay xizmatlar siz uchun!"
    ),
    "🛂 Visa Xizmatlari": (
        "🛂 Visa Xizmatlari:\n"
        "• Turistik: $120\n"
        "• Umra: $160\n\n"
        "Vizasi yo‘q mijozlarga tezkor yordam!"
    ),
    "🌙 Ravza Ruxsatnomalari": (
        "🌙 Ravza (Rawda) ruxsatnomalari:\n"
        "• Vizasi borlarga: 15 SAR\n"
        "• Vizasi yo‘qlarga: 20 SAR\n"
        "• Guruh uchun chegirmalar mavjud."
    ),
    "🚗 Transport Xizmatlari": (
        "🚗 Transport:\n"
        "• Avtobus, Taksi, Shaxsiy avtomobil\n"
        "• Yo‘nalish va narxlar uchun biz bilan bog‘laning."
    ),
    "🚆 Po‘ezd Biletlar": (
        "🚆 Po‘ezd yo‘nalishlari:\n"
        "• Madina - Makka\n"
        "• Riyadh - Dammam\n"
        "• Narxlar yo‘nalishga qarab belgilanadi."
    ),
    "✈️ Aviabiletlar": (
        "✈️ Aviabiletlar:\n"
        "• Dunyo bo‘ylab yo‘nalishlar\n"
        "• Narxlar mijoz talabiga ko‘ra\n"
        "• Malakali mutaxassislar yordam beradi."
    ),
    "🍽️ Guruh Ovqatlar": (
        "🍽️ Ovqat Xizmatlari:\n"
        "• 10+ kishilik guruhlar uchun\n"
        "• Milliy va xalqaro taomlar\n"
        "• Sifatli va xavfsiz xizmat."
    )
}

payment_text = (
    "\n💳 To‘lov usullari:\n"
    "- Bank karta\n- PayMe, Click, Apelsin\n- Naqd manager orqali\n\n"
    "To‘lovdan so‘ng kvitansiyani yuboring."
)

# --- Start ---
@dp.message_handler(commands=["start", "help"])
async def start_handler(message: types.Message):
    await message.answer(
        f"Assalomu alaykum {message.from_user.full_name}!\n"
        "UmraJet botiga xush kelibsiz. Xizmat turini tanlang:",
        reply_markup=main_menu
    )

# --- Xizmat tanlash ---
@dp.message_handler(lambda msg: msg.text in services)
async def choose_service(message: types.Message, state: FSMContext):
    await state.update_data(service=message.text)
    await OrderStates.confirming_order.set()
    await message.answer(
        services[message.text] + payment_text,
        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("✅ Buyurtma berish").add("🔙 Orqaga")
    )

# --- Orqaga ---
@dp.message_handler(lambda msg: msg.text == "🔙 Orqaga", state="*")
async def go_back(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Asosiy menyu", reply_markup=main_menu)

# --- Buyurtma tasdiqlash ---
@dp.message_handler(lambda msg: msg.text == "✅ Buyurtma berish", state=OrderStates.confirming_order)
async def confirm_order(message: types.Message, state: FSMContext):
    data = await state.get_data()
    service = data.get("service")

    text = (
        f"🆕 Yangi buyurtma!\n"
        f"👤 Foydalanuvchi: {message.from_user.full_name}\n"
        f"🆔 ID: {message.from_user.id}\n"
        f"📦 Xizmat: {service}"
    )

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text)
        except:
            pass

    await message.answer("Buyurtmangiz qabul qilindi! Managerlar siz bilan bog‘lanadi.", reply_markup=main_menu)
    await state.finish()

# --- Admin Panel ---
@dp.message_handler(commands=["admin"])
async def admin_panel(message: types.Message):
    if message.from_user.id in ADMIN_IDS:
        await message.answer("🔐 Admin panel: foydalanuvchilar statistikasi va buyurtmalarni boshqarish (beta).")
    else:
        await message.answer("⛔ Sizda admin ruxsati yo‘q.")

# --- Boshqa xabarlar ---
@dp.message_handler()
async def fallback(message: types.Message):
    await message.answer("Iltimos, menyudan xizmatni tanlang yoki /start buyrug‘ini bering.")

# --- Run ---
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
