import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# Logger sozlash
logging.basicConfig(level=logging.INFO)

# .env dan o'qish uchun
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = os.getenv("ADMIN_IDS")  # string, vergul bilan bo'lingan IDlar
GROUP_ID = os.getenv("GROUP_ID")

if not BOT_TOKEN or not ADMIN_IDS or not GROUP_ID:
    logging.error("Iltimos .env faylini to'liq va to'g'ri to'ldiring!")
    exit()

ADMIN_IDS = list(map(int, ADMIN_IDS.split(',')))
GROUP_ID = int(GROUP_ID)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- Holatlar (States) ---
class OrderStates(StatesGroup):
    choosing_service = State()
    confirming_order = State()
    waiting_payment = State()

# --- Menyular va kalitlar ---
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

# --- Xizmatlar matnlari va narxlar ---
services_info = {
    "umra_paket": {
        "name": "Umra Paketlari",
        "description": (
            "Umra safaringizni mukammal qiling! 📿\n"
            "✅ Oddiy Paket: $1100 dan\n"
            "✅ VIP Paket: $2000 dan\n"
            "✅ Paketga quyidagilar kiradi:\n"
            "- Parvoz, mehmonxona\n"
            "- Transport, guruh ovqatlar\n"
            "- Tasarruf va qo‘llab-quvvatlash\n\n"
            "Siz uchun qulay va sifatli xizmatlar."
        ),
    },
    "visa": {
        "name": "Visa Xizmatlari",
        "description": (
            "Visa olish xizmatlari:\n"
            "🛂 Turist Visa: $120 dona uchun\n"
            "🕋 Umra Visa: $160 dona uchun\n\n"
            "Eslatma: Visa faqat avval ro‘yxatdan o‘tmagan va Ravza ruxsatnomasi olinmagan mijozlar uchun. "
            "Agar vizangiz bor bo‘lsa, bizda mavjud vizalarga xizmat ko‘rsatamiz."
        ),
    },
    "ravza": {
        "name": "Ravza Ruxsatnomalari",
        "description": (
            "Ravza (Rawda) ruxsatnomalari:\n"
            "🎟️ Vizasi bo‘lganlarga: 15 SAR/dona\n"
            "🎟️ Vizasi bo‘lmaganlarga: 20 SAR/dona\n\n"
            "Guruhlar uchun arzonroq narxlar.\n"
            "Ruxsatnoma olish uchun vizangizning mavjudligi muhim."
        ),
    },
    "transport": {
        "name": "Transport Xizmatlari",
        "description": "Sizga qulay transport xizmatlari:\n- Avtobus, Taksi, Shaxsiy transport.\nNarxlar va batafsil ma’lumot uchun murojaat qiling.",
    },
    "train": {
        "name": "Po‘ezd Biletlar",
        "description": (
            "HHR Po‘ezd yo‘nalishlari uchun biletlar:\n"
            "• Madina - Makka\n"
            "• Madina - Riyadh\n"
            "• Riyadh - Dammam\n"
            "Narxlar yo‘nalishga qarab o‘zgaradi.\n"
            "Batafsil ma’lumot uchun biz bilan bog‘laning."
        ),
    },
    "avia": {
        "name": "Aviabiletlar",
        "description": (
            "Dunyoning istalgan nuqtasiga aviachipta xizmatlari.\n"
            "Yo‘nalish va narxlar mijoz talabiga qarab belgilanadi.\n"
            "Bizning mutaxassislarimiz sizga yordam beradi."
        ),
    },
    "food": {
        "name": "Guruh Ovqatlar",
        "description": (
            "Katta guruhlar uchun maxsus ovqat xizmatlari.\n"
            "Turli milliy taomlar, sifatli xizmat.\n"
            "Narx va menyu haqida batafsil ma’lumot uchun murojaat qiling."
        ),
    }
}

# --- To'lov usullari ---
payment_info = (
    "To‘lov usullari:\n"
    "💳 Bank kartalari orqali to‘lov\n"
    "📲 PayMe, Click, Apelsin kabi elektron to‘lovlar\n"
    "🤝 Managerlar orqali naqd to‘lov\n\n"
    "To‘lovni amalga oshirganingizdan so‘ng, iltimos, kvitansiyani yuboring."
)

# --- Handlerlar ---
@dp.message_handler(commands=["start", "help"])
async def cmd_start(message: types.Message):
    await message.answer(
        f"Assalomu alaykum, {message.from_user.full_name}!\n"
        "UmraJet Botga xush kelibsiz! 🌟\n\n"
        "Quyidagi xizmatlardan birini tanlang:",
        reply_markup=main_menu_kb
    )


@dp.message_handler(lambda m: m.text in [info["name"] for info in services_info.values()])
async def service_menu(message: types.Message):
    # Xizmat nomi orqali aniqlash
    chosen_service = None
    for key, info in services_info.items():
        if message.text == info["name"]:
            chosen_service = key
            break
    if chosen_service:
        await message.answer(
            f"📌 {services_info[chosen_service]['name']} haqida ma’lumot:\n\n"
            f"{services_info[chosen_service]['description']}\n\n"
            f"{payment_info}\n\n"
            "Buyurtma berish uchun *Buyurtma berish* tugmasini bosing.",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("✅ Buyurtma berish").add("🔙 Orqaga")
        )
        await OrderStates.choosing_service.set()
        await dp.current_state(user=message.from_user.id).update_data(service=chosen_service)
    else:
        await message.answer("Kechirasiz, bunday xizmat mavjud emas.")


@dp.message_handler(lambda m: m.text == "🔙 Orqaga", state='*')
async def go_back(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "Asosiy menyu:",
        reply_markup=main_menu_kb
    )


@dp.message_handler(lambda m: m.text == "❌ Bekor qilish", state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Buyurtma bekor qilindi. Asosiy menyu:", reply_markup=main_menu_kb)


@dp.message_handler(lambda m: m.text == "✅ Buyurtma berish", state=OrderStates.choosing_service)
async def order_confirm(message: types.Message, state: FSMContext):
    data = await state.get_data()
    service = data.get("service")
    if service:
        await message.answer(
            f"Buyurtmangizni tasdiqlaysizmi? \nXizmat: {services_info[service]['name']}",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("✅ Tasdiqlash").add("❌ Bekor qilish")
        )
        await OrderStates.confirming_order.set()
    else:
        await message.answer("Xizmat tanlanmadi. Iltimos, qayta tanlang.")
        await state.finish()


@dp.message_handler(lambda m: m.text == "✅ Tasdiqlash", state=OrderStates.confirming_order)
async def process_order(message: types.Message, state: FSMContext):
    data = await state.get_data()
    service = data.get("service")
    user_id = message.from_user.id
    full_name = message.from_user.full_name

    # Bu yerda siz orderni DB yoki faylga saqlashingiz mumkin
    # Hozircha managerlarga xabar yuboramiz

    text = (
        f"🆕 Yangi buyurtma!\n"
        f"👤 Foydalanuvchi: {full_name} (ID: {user_id})\n"
        f"📦 Xizmat: {services_info[service]['name']}\n"
        "⏳ Holat: To‘lov kutilmoqda."
    )

    # Adminlarga xabar yuborish
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text)
        except Exception as e:
            logging.error(f"Adminga xabar yuborishda xato: {e}")

    await message.answer(
        "Buyurtmangiz qabul qilindi! Tez orada managerlar siz bilan bog‘lanadi.\n"
        "To‘lovni amalga oshirgach, kvitansiyani yuboring.",
        reply_markup=main_menu_kb
    )
    await state.finish()


@dp.message_handler(state='*', content_types=types.ContentTypes.ANY)
async def default_handler(message: types.Message, state: FSMContext):
    await message.answer("Iltimos, menyudan xizmatni tanlang yoki /start buyrug‘ini bering.")


# --- Admin komandalar ---
@dp.message_handler(commands=["admin"], user_id=ADMIN_IDS)
async def admin_panel(message: types.Message):
    users_count = "Noma'lum"  # DB bo‘lsa, shu yerda hisoblash mumkin
    text = (
        f"Admin paneliga xush kelibsiz!\n"
        f"Foydalanuvchilar soni: {users_count}\n"
        "Buyurtmalarni ko‘rish va boshqarish funktsiyasi hozircha ishlab chiqilmoqda."
    )
    await message.answer(text)


# --- Bot ishga tushishi ---
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
