import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = os.getenv("ADMIN_IDS")
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
    choosing_payment_method = State()
    waiting_payment = State()

# --- Menyular ---
main_menu_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_menu_kb.add("🕋 Umra Paketlari", "🛂 Visa Xizmatlari")
main_menu_kb.add("🌙 Ravza Ruxsatnomalari", "🚗 Transport Xizmatlari")
main_menu_kb.add("🚆 Po‘ezd Biletlar", "✈️ Aviabiletlar")
main_menu_kb.add("🍽️ Guruh Ovqatlar")

cancel_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
cancel_kb.add("❌ Bekor qilish")

back_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
back_kb.add("🔙 Orqaga", "❌ Bekor qilish")

payment_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
payment_kb.add("Uzcard", "Humo")
payment_kb.add("Visa", "Crypto")
payment_kb.add("❌ Bekor qilish")

# --- Ma'lumotlar ---
services_info = {
    "umra_paket": {
        "name": "🕋 Umra Paketlari",
        "description": "Umra safaringiz uchun mukammal paketlar...",
        "managers": ["@vip_arabiy", "@V001VB"]
    },
    "visa": {
        "name": "🛂 Visa Xizmatlari",
        "description": "Visa xizmatlari...",
        "managers": ["@vip_arabiy", "@V001VB"]
    },
    "ravza": {
        "name": "🌙 Ravza Ruxsatnomalari",
        "description": "Rawda ruxsatnomalari...",
        "managers": ["@vip_arabiy", "@V001VB"]
    },
    "transport": {
        "name": "🚗 Transport Xizmatlari",
        "description": "Transport xizmatlari...",
        "managers": ["@vip_arabiy", "@V001VB"]
    },
    "train": {
        "name": "🚆 Po‘ezd Biletlar",
        "description": "Po‘ezd yo‘nalishlari...",
        "managers": ["@vip_arabiy", "@V001VB"]
    },
    "avia": {
        "name": "✈️ Aviabiletlar",
        "description": "Dunyo bo‘ylab aviachipta xizmati...",
        "managers": ["@vip_arabiy", "@V001VB"]
    },
    "food": {
        "name": "🍽️ Guruh Ovqatlar",
        "description": "Katta guruhlar uchun maxsus ovqat xizmatlari...",
        "managers": ["@vip_arabiy", "@V001VB"]
    },
}

channels_text = "🔹 @umrajet\n🔹 @the_ravza"

def format_managers(managers):
    return ", ".join(managers)

# --- Handlerlar ---

@dp.message_handler(commands=["start", "help"])
async def cmd_start(message: types.Message):
    text = f"Assalomu alaykum, {message.from_user.full_name}!\n\nUmraJet Botga xush kelibsiz! 🌟\n"
    for s in services_info.values():
        text += f"\n{s['name']}"
    text += f"\n\nRasmiy kanallar:\n{channels_text}"
    await message.answer(text, reply_markup=main_menu_kb)

@dp.message_handler(lambda m: m.text in [s['name'] for s in services_info.values()])
async def service_info_handler(message: types.Message, state: FSMContext):
    for key, val in services_info.items():
        if val['name'] == message.text:
            await state.update_data(service=key)
            desc = val['description'] + f"\n\nMenejerlar: {format_managers(val['managers'])}"
            await message.answer(desc, reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("✅ Buyurtma berish", "🔙 Orqaga"))
            await OrderStates.choosing_service.set()
            return

@dp.message_handler(lambda m: m.text == "✅ Buyurtma berish", state=OrderStates.choosing_service)
async def confirm_order(message: types.Message):
    await message.answer("To‘lov turini tanlang:", reply_markup=payment_kb)
    await OrderStates.choosing_payment_method.set()

@dp.message_handler(lambda m: m.text in ["Uzcard", "Humo", "Visa", "Crypto"], state=OrderStates.choosing_payment_method)
async def send_payment_info(message: types.Message, state: FSMContext):
    payment_text = {
        "Uzcard": "💳 *Uzcard:*\n1. 8600 0304 9680 2624 (Khamidov Ibodulloh)\n2. 5614 6822 1222 3368 (Khamidov Ibodulloh)",
        "Humo": "💳 *Humo:*\n9860 1001 2621 9243 (Khamidov Ibodulloh)",
        "Visa": "💳 *Visa:*\n1. 4140 8400 0184 8680 (Khamidov Ibodulloh)\n2. 4278 3100 2389 5840 (Khamidov Ibodulloh)",
        "Crypto": "🪙 *Crypto:*\nUSDT (TRC20): `TLGiUsNzQ8n31x3VwsYiWEU97jdftTDqT3`\nETH/BTC (BEP20): `0xa11fb72cc1ee74cfdaadb25ab2530dd32bafa8f8`"
    }[message.text]
    await message.answer(payment_text + "\n\n📥 To‘lovdan so‘ng kvitansiyani yuboring", parse_mode="Markdown", reply_markup=back_kb)
    await OrderStates.waiting_payment.set()

@dp.message_handler(lambda m: m.text in ["🔙 Orqaga", "❌ Bekor qilish"], state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Bosh menyu:", reply_markup=main_menu_kb)

@dp.message_handler(content_types=types.ContentTypes.DOCUMENT, state=OrderStates.waiting_payment)
async def payment_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    service_key = data.get("service")
    info = services_info.get(service_key)

    order_text = (
        f"🆕 Yangi buyurtma!\n"
        f"Foydalanuvchi: {message.from_user.full_name} (ID: {message.from_user.id})\n"
        f"Xizmat: {info['name']}\n"
        f"Managerlar: {format_managers(info['managers'])}"
    )
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, order_text)
            await bot.send_document(admin_id, message.document.file_id)
        except Exception as e:
            logging.error(f"Admin ID {admin_id} uchun xato: {e}")

    await message.answer("To‘lov qabul qilindi. Tez orada menejerlar siz bilan bog‘lanishadi.", reply_markup=main_menu_kb)
    await state.finish()

@dp.message_handler()
async def fallback_handler(message: types.Message):
    await message.answer("Iltimos, menyudan tanlang yoki /start buyrug‘ini bosing.", reply_markup=main_menu_kb)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
