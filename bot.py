import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from dotenv import load_dotenv

# --- 1. .env dan token va adminlarni yuklash ---
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))  # misol: "123456,654321"
GROUP_ID = int(os.getenv("GROUP_ID", "0"))

if not BOT_TOKEN or not ADMIN_IDS or not GROUP_ID:
    logging.error("❌ BOT_TOKEN, ADMIN_IDS yoki GROUP_ID .env faylida noto‘g‘ri yoki bo‘sh!")
    exit()

# --- 2. Logger sozlash ---
logging.basicConfig(level=logging.INFO)

# --- 3. Bot va dispatcher ---
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- 4. FSM holatlar ---
class OrderStates(StatesGroup):
    choosing_service = State()
    confirming_order = State()
    choosing_payment = State()
    waiting_payment = State()

# --- 5. Tugmalar va menyular ---
main_menu_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
main_menu_kb.add(
    "🕋 Umra Paketlari", "🛂 Visa Xizmatlari",
    "🌙 Ravza Ruxsatnomalari", "🚗 Transport Xizmatlari",
    "🚆 Po‘ezd Biletlar", "✈️ Aviabiletlar",
    "🍽️ Guruh Ovqatlar"
)

back_cancel_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
back_cancel_kb.add("🔙 Orqaga", "❌ Bekor qilish")

def payment_buttons():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("💳 Uzcard", "💳 Humo", "💳 Visa", "💰 Crypto", "🔙 Orqaga")
    return kb

def back_cancel_buttons():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔙 Orqaga", "❌ Bekor qilish")
    return kb

# --- 6. Xizmatlar tavsifi (premium marketing uslubida) ---
services = {
    "umra_paket": {
        "title": "🕋 Umra Paketlari",
        "desc": (
            "🌟 <b>Umra Paketlari bilan Orzularingizni Ro‘yobga Chiqarish Vaqti Keldi!</b>\n\n"
            "🔸 <b>Oddiy Paket</b> — $1100 dan boshlanadi\n"
            "🔸 <b>VIP Paket</b> — $2000 dan yuqori\n\n"
            "✅ Paketga quyidagilar kiradi:\n"
            "- Komfortli mehmonxona joylashuvi\n"
            "- Shaxsiy transport va ekskursiyalar\n"
            "- Maxsus guruh ovqatlar\n"
            "- 24/7 qo‘llab-quvvatlash va ekspert maslahatlari\n\n"
            "Biz bilan sayohatingiz qulay, xavfsiz va unutilmas bo‘ladi! "
            "Orzularingizga yaqinlashing, bugun buyurtma bering!"
        ),
        "managers": ["@vip_arabiy", "@V001VB"]
    },
    "visa": {
        "title": "🛂 Visa Xizmatlari",
        "desc": (
            "🛂 <b>Tez va Ishonchli Visa Xizmati!</b>\n\n"
            "⏰ Ish jarayoni tez va oson\n"
            "💰 Narxlar:\n"
            "- Turist Visa: <b>$120</b>\n"
            "- Umra Visa: <b>$160</b>\n\n"
            "Vizangizni ishonchli qo‘llarga topshiring — qolganini biz bajaramiz.\n"
            "Bugun murojaat qiling, tezroq natijaga erishing!"
        ),
        "managers": ["@vip_arabiy", "@V001VB"]
    },
    "ravza": {
        "title": "🌙 Ravza Ruxsatnomalari",
        "desc": (
            "🌟 <b>Maxsus Ravza Ruxsatnomalari Xizmati</b>\n\n"
            "🎟️ Vizasi borlarga — <b>15 SAR</b>\n"
            "🎟️ Vizasi yo‘qlarga — <b>20 SAR</b>\n\n"
            "Guruhlar uchun chegirmalar mavjud.\n"
            "Sizni Ravzada qulay va xavfsiz dam olish kutmoqda.\n"
            "Hozir bog‘laning, imkoniyatni qo‘ldan boy bermang!"
        ),
        "managers": ["@vip_arabiy", "@V001VB"]
    },
    "transport": {
        "title": "🚗 Transport Xizmatlari",
        "desc": (
            "🚐 <b>Shaxsiy va Guruh Transport Xizmatlari</b>\n\n"
            "✔️ Avtobuslar, taksilar va VIP transportlar\n"
            "✔️ Qulay va ishonchli yo‘lovchi tashish\n\n"
            "Narx va qo‘shimcha ma’lumot uchun managerlarimizga murojaat qiling.\n"
            "Sayohatingiz uchun eng qulay transportni biz bilan tanlang!"
        ),
        "managers": ["@vip_arabiy", "@V001VB"]
    },
    "train": {
        "title": "🚆 Po‘ezd Biletlar",
        "desc": (
            "🚄 <b>Xavfsiz va qulay po‘ezd safarlari!</b>\n\n"
            "Mashhur yo‘nalishlar:\n"
            "- Madina – Makka\n"
            "- Riyadh – Dammam\n\n"
            "Narxlar yo‘nalishga qarab o‘zgaradi.\n"
            "Qo‘shimcha ma’lumot va bronlash uchun managerlarga murojaat qiling."
        ),
        "managers": ["@vip_arabiy", "@V001VB"]
    },
    "avia": {
        "title": "✈️ Aviabiletlar",
        "desc": (
            "🌍 <b>Dunyo bo‘ylab eng qulay va arzon aviabiletlar!</b>\n\n"
            "Siz tanlagan manzilga eng maqbul chiptalarni topamiz.\n"
            "Qo‘shimcha ma’lumot uchun managerlarimizga yozing."
        ),
        "managers": ["@vip_arabiy", "@V001VB"]
    },
    "food": {
        "title": "🍽️ Guruh Ovqatlar",
        "desc": (
            "🥘 <b>Mahalliy va xalqaro taomlar guruhlar uchun tayyorlanadi.</b>\n\n"
            "Sifatli va xilma-xil menyu, shaxsiy yondashuv.\n"
            "Savollar uchun managerlarga murojaat qiling.\n"
            "Sizning qulayligingiz biz uchun muhim!"
        ),
        "managers": ["@vip_arabiy", "@V001VB"]
    }
}

# --- 7. To‘lov ma’lumotlari ---
payments = {
    "Uzcard": (
        "💳 <b>Uzcard to‘lovlari:</b>\n\n"
        "1️⃣ <code>8600 0304 9680 2624</code> (Khamidov Ibodulloh)\n"
        "2️⃣ <code>5614 6822 1222 3368</code> (Khamidov Ibodulloh)"
    ),
    "Humo": (
        "💳 <b>Humo to‘lovlari:</b>\n\n"
        "<code>9860 1001 2621 9243</code> (Khamidov Ibodulloh)"
    ),
    "Visa": (
        "💳 <b>Visa to‘lovlari:</b>\n\n"
        "1️⃣ <code>4140 8400 0184 8680</code> (Khamidov Ibodulloh)\n"
        "2️⃣ <code>4278 3100 2389 5840</code> (Khamidov Ibodulloh)"
    ),
    "Crypto": (
        "💰 <b>Kripto to‘lovlari:</b>\n\n"
        "USDT (Tron TRC20):\n<code>TLGiUsNzQ8n31x3VwsYiWEU97jdftTDqT3</code>\n\n"
        "ETH (BEP20):\n<code>0xa11fb72cc1ee74cfdaadb25ab2530dd32bafa8f8</code>\n\n"
        "BTC (BEP20):\n<code>0x8e9a10874f910244932420ba521f0c92e67414d2</code>"
    )
}

# --- 8. Qo‘shimcha o‘zgaruvchilar ---
services_titles = [s["title"] for s in services.values()]

# --- 9. Handlerlar ---

@dp.message_handler(commands=["start", "help"])
async def start_handler(message: types.Message):
    text = (
        f"👋 Assalomu alaykum, {message.from_user.full_name}!\n\n"
        f"<b>UmraJet Botga xush kelibsiz! 🌟</b>\n\n"
        "Quyidagi xizmatlardan birini tanlang:\n\n"
        "🕋 <b>Umra Paketlari</b>\n"
        "🛂 <b>Visa Xizmatlari</b>\n"
        "🌙 <b>Ravza Ruxsatnomalari</b>\n"
        "🚗 <b>Transport Xizmatlari</b>\n"
        "🚆 <b>Po‘ezd Biletlar</b>\n"
        "✈️ <b>Aviabiletlar</b>\n"
        "🍽️ <b>Guruh Ovqatlar</b>\n\n"
        "📢 <b>Rasmiy kanallarimiz:</b>\n"
        "🔹 <a href='https://t.me/umrajet'>@umrajet</a>\n"
        "🔹 <a href='https://t.me/the_ravza'>@the_ravza</a>\n\n"
        "👨‍💼 <b>Bog‘lanish uchun mas’ul managerlar:</b>\n"
        "🔹 <a href='https://t.me/vip_arabiy'>@vip_arabiy</a> — Asosiy manager\n"
        "🔹 <a href='https://t.me/V001VB'>@V001VB</a> — Zaxira manager"
    )
    await message.answer(text, reply_markup=main_menu_kb, parse_mode="HTML", disable_web_page_preview=True)
    await OrderStates.choosing_service.set()

@dp.message_handler(lambda m: m.text in services_titles, state=OrderStates.choosing_service)
async def show_service_handler(message: types.Message, state: FSMContext):
    service = next((v for v in services.values() if v["title"] == message.text), None)
    if service is None:
        await message.answer("❌ Noto‘g‘ri xizmat tanlandi. Iltimos, menyudan tanlang.")
        return
    desc = service["desc"]
    managers = ", ".join(service["managers"])
    text = f"{desc}\n\n👨‍💼 <b>Managerlar:</b> {managers}\n\n" \
           "Xizmatdan foydalanishni tasdiqlaysizmi?"
    await message.answer(text, reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("✅ Tasdiqlayman", "🔙 Orqaga"), parse_mode="HTML")
    await state.update_data(service=service["title"])
    await OrderStates.next()  # confirming_order

@dp.message_handler(lambda m: m.text == "✅ Tasdiqlayman", state=OrderStates.confirming_order)
async def confirm_order_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    service = data.get("service")
    if not service:
        await message.answer("❌ Xizmat tanlanmadi. Iltimos, boshidan tanlang.")
        await OrderStates.choosing_service.set()
        return
    text = (
        "To‘lov usulini tanlang:\n\n"
        "💳 Uzcard\n"
        "💳 Humo\n"
        "💳 Visa\n"
        "💰 Crypto"
    )
    await message.answer(text, reply_markup=payment_buttons())
    await OrderStates.next()  # choosing_payment

@dp.message_handler(lambda m: m.text in ["💳 Uzcard", "💳 Humo", "💳 Visa", "💰 Crypto"], state=OrderStates.choosing_payment)
async def payment_method_handler(message: types.Message, state: FSMContext):
    payment_method = message.text.strip()
    if payment_method == "💳 Uzcard":
        key = "Uzcard"
    elif payment_method == "💳 Humo":
        key = "Humo"
    elif payment_method == "💳 Visa":
        key = "Visa"
    elif payment_method == "💰 Crypto":
        key = "Crypto"
    else:
        await message.answer("❌ Noto‘g‘ri to‘lov usuli tanlandi.")
        return

    payment_info = payments.get(key)
    if not payment_info:
        await message.answer("❌ To‘lov ma’lumotlari topilmadi.")
        return

    await message.answer(
        payment_info + "\n\nTo‘lovni amalga oshirgach, tasdiqlash uchun xabar yuboring.",
        reply_markup=back_cancel_buttons(),
        parse_mode="HTML"
    )
    await state.update_data(payment_method=key)
    await OrderStates.waiting_payment.set()

@dp.message_handler(lambda m: m.text == "🔙 Orqaga", state="*")
async def go_back_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == OrderStates.confirming_order.state:
        await OrderStates.choosing_service.set()
        await message.answer("🔙 Asosiy xizmatlar menyusiga qaytdingiz.", reply_markup=main_menu_kb)
    elif current_state == OrderStates.choosing_payment.state:
        await OrderStates.confirming_order.set()
        await message.answer("🔙 Xizmat tasdiqlash menyusiga qaytdingiz.", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("✅ Tasdiqlayman", "🔙 Orqaga"))
    elif current_state == OrderStates.waiting_payment.state:
        await OrderStates.choosing_payment.set()
        await message.answer("🔙 To‘lov usulini tanlash menyusiga qaytdingiz.", reply_markup=payment_buttons())
    else:
        await message.answer("🔙 Siz bosh menyudasiz.", reply_markup=main_menu_kb)
        await OrderStates.choosing_service.set()

@dp.message_handler(lambda m: m.text == "❌ Bekor qilish", state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("❌ Buyurtma bekor qilindi. Bosh menyuga qaytdingiz.", reply_markup=main_menu_kb)

@dp.message_handler(state=OrderStates.waiting_payment)
async def payment_confirmation_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    service_title = data.get("service")
    payment_method = data.get("payment_method")
    if not service_title or not payment_method:
        await message.answer("❌ Ma'lumotlar to‘liq emas. Iltimos, boshidan boshlang.")
        await state.finish()
        return

    # Adminlarga xabar yuborish
    service = next((v for v in services.values() if v["title"] == service_title), None)
    user = message.from_user
    managers = service["managers"] if service else []
    text = (
        f"✅ <b>Yangi buyurtma qabul qilindi!</b>\n\n"
        f"👤 Foydalanuvchi: <a href='tg://user?id={user.id}'>{user.full_name}</a>\n"
        f"📱 Telegram: @{user.username if user.username else 'yo‘q'}\n"
        f"🕋 Xizmat: {service_title}\n"
        f"💳 To‘lov usuli: {payment_method}\n"
        f"⏰ Vaqt: {message.date.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"📲 Iltimos, tez orada bog‘laning!"
    )
    # Guruhga xabar yuborish
    await bot.send_message(GROUP_ID, text, parse_mode="HTML", disable_web_page_preview=True)

    # Har bir managerga shaxsiy xabar yuborish
    for mgr_username in managers:
        try:
            await bot.send_message(mgr_username, text, parse_mode="HTML", disable_web_page_preview=True)
        except Exception as e:
            logging.error(f"Managerga xabar yuborishda xato: {mgr_username} — {e}")

    await message.answer("✅ Buyurtmangiz qabul qilindi! Tez orada managerlarimiz siz bilan bog‘lanadi.", reply_markup=main_menu_kb)
    await state.finish()

@dp.message_handler()
async def fallback_handler(message: types.Message):
    await message.answer("❓ Iltimos, menyudan xizmat tanlang yoki /start komandasini yuboring.", reply_markup=main_menu_kb)

# --- 10. Botni ishga tushurish ---
if __name__ == "__main__":
    logging.info("Bot ishga tushmoqda...")
    executor.start_polling(dp, skip_updates=True)
