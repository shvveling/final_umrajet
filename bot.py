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
main_menu = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
main_menu.add(
    "🕋 Umra Paketlari", "🛂 Visa Xizmatlari",
    "🌙 Ravza Ruxsatnomalari", "🚗 Transport Xizmatlari",
    "🚆 Po‘ezd Biletlar", "✈️ Aviabiletlar",
    "🍽️ Guruh Ovqatlar"
)

back_cancel_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
back_cancel_kb.add("🔙 Orqaga", "❌ Bekor qilish")

payment_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
payment_kb.add("💳 Uzcard", "💳 Humo", "💳 Visa", "💰 Crypto", "🔙 Orqaga")

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

# --- 7. To‘lov ma’lumotlari (ancha chiroyli va copy-paste uchun) ---
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
        "BTC (BEP20):\n<code>0xa11fb72cc1ee74cfdaadb25ab2530dd32bafa8f8</code>"
    )
}

channels = "📢 Rasmiy kanallar:\n@umrajet\n@the_ravza"

# --- 8. Foydali funksiyalar ---
def managers_to_str(managers_list):
    return ", ".join(managers_list)

def payment_buttons():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("💳 Uzcard", "💳 Humo", "💳 Visa", "💰 Crypto", "🔙 Orqaga")
    return kb

def back_cancel_buttons():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔙 Orqaga", "❌ Bekor qilish")
    return kb

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
    
# --- 10. Xizmat tanlash handleri ---
@dp.message_handler(lambda m: m.text in [s["title"] for s in services.values()])
async def service_show(message: types.Message, state: FSMContext):
    for key, val in services.items():
        if val["title"] == message.text:
            await state.update_data(service_key=key)
            text = (
                f"<b>{val['title']}</b>\n\n"
                f"{val['desc']}\n\n"
                f"<b>Managerlar:</b> {managers_to_str(val['managers'])}\n\n"
                "Buyurtma berish uchun pastdagi tugmani bosing."
            )
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("✅ Buyurtma berish", "🔙 Orqaga")
            await message.answer(text, parse_mode="HTML", reply_markup=kb)
            await OrderStates.choosing_service.set()
            return

# --- 11. Buyurtma berish bosqichi ---
@dp.message_handler(lambda m: m.text == "✅ Buyurtma berish", state=OrderStates.choosing_service)
async def order_confirm(message: types.Message, state: FSMContext):
    data = await state.get_data()
    service_key = data.get("service_key")
    if not service_key or service_key not in services:
        await message.answer("Xizmat topilmadi, boshidan tanlang.", reply_markup=main_menu)
        await state.finish()
        return

    service = services[service_key]
    text = (
        f"Siz <b>{service['title']}</b> xizmatini tanladingiz.\n\n"
        "Iltimos, qulay to‘lov tizimini tanlang:"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=payment_buttons())
    await OrderStates.choosing_payment.set()

# --- 12. To‘lov tizimini tanlash ---
@dp.message_handler(lambda m: m.text in ["💳 Uzcard", "💳 Humo", "💳 Visa", "💰 Crypto"], state=OrderStates.choosing_payment)
async def payment_info(message: types.Message, state: FSMContext):
    pay_method = message.text.replace("💳 ", "").replace("💰 ", "")
    text = payments.get(pay_method)
    if not text:
        await message.answer("Kechirasiz, ushbu to‘lov turi hozircha mavjud emas.", reply_markup=payment_buttons())
        return

    data = await state.get_data()
    service_key = data.get("service_key")
    service = services.get(service_key)

    confirm_text = (
        f"Siz <b>{service['title']}</b> xizmatini tanladingiz va "
        f"<b>{pay_method}</b> orqali to‘lov qilmoqchisiz.\n\n"
        f"{text}\n\n"
        "To‘lovni amalga oshirgandan so‘ng, tasdiqlash uchun shaxsiy xabar yuboring.\n"
        f"{channels}"
    )
    await message.answer(confirm_text, parse_mode="HTML", reply_markup=back_cancel_buttons())
    await OrderStates.waiting_payment.set()
    await state.update_data(payment_method=pay_method)

# --- 13. To‘lov tasdiqlash ---
@dp.message_handler(state=OrderStates.waiting_payment)
async def payment_done(message: types.Message, state: FSMContext):
    if message.text in ["🔙 Orqaga"]:
        # Orqaga qaytish
        await message.answer("To‘lov tizimini tanlash menyusiga qaytdingiz.", reply_markup=payment_buttons())
        await OrderStates.choosing_payment.set()
        return
    elif message.text in ["❌ Bekor qilish"]:
        await message.answer("Buyurtma bekor qilindi.", reply_markup=main_menu)
        await state.finish()
        return

    # Tasdiqlash deb qabul qilamiz va adminlarga xabar yuboramiz
    data = await state.get_data()
    service_key = data.get("service_key")
    payment_method = data.get("payment_method")
    service = services.get(service_key)

    user = message.from_user
    order_msg = (
        f"🆕 <b>Yangi buyurtma</b>!\n\n"
        f"👤 Foydalanuvchi: {user.full_name} (@{user.username if user.username else 'yo‘q'})\n"
        f"📱 ID: <code>{user.id}</code>\n"
        f"🕋 Xizmat: <b>{service['title']}</b>\n"
        f"💳 To‘lov turi: <b>{payment_method}</b>\n"
        f"✉️ To‘lov haqida xabar:\n<code>{message.text}</code>"
    )

    # Adminlarga yuborish
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, order_msg, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Adminga xabar yuborishda xato: {e}")

    # Guruhga yuborish
    try:
        await bot.send_message(GROUP_ID, order_msg, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Guruhga xabar yuborishda xato: {e}")

    await message.answer("Buyurtmangiz qabul qilindi! Tez orada siz bilan bog‘lanamiz. 🙏", reply_markup=main_menu)
    await state.finish()

# --- 14. Orqaga va bekor qilish tugmalari umumiy ishlovi ---
@dp.message_handler(lambda m: m.text == "🔙 Orqaga", state="*")
async def go_back(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == OrderStates.choosing_payment.state:
        await message.answer("Xizmat tanlash menyusiga qaytdingiz.", reply_markup=main_menu)
        await state.finish()
    elif current_state == OrderStates.waiting_payment.state:
        await message.answer("To‘lov tizimini tanlash menyusiga qaytdingiz.", reply_markup=payment_buttons())
        await OrderStates.choosing_payment.set()
    elif current_state == OrderStates.choosing_service.state:
        await message.answer("Asosiy menyuga qaytdingiz.", reply_markup=main_menu)
        await state.finish()
    else:
        await message.answer("Asosiy menyuga qaytdingiz.", reply_markup=main_menu)
        await state.finish()

@dp.message_handler(lambda m: m.text == "❌ Bekor qilish", state="*")
async def cancel_order(message: types.Message, state: FSMContext):
    await message.answer("Buyurtma bekor qilindi.", reply_markup=main_menu)
    await state.finish()

# --- 15. Noma’lum buyruq yoki xato matn ---
@dp.message_handler()
async def unknown_msg(message: types.Message):
    await message.answer("Iltimos, menyudan xizmat tanlang yoki /start ni bosing.", reply_markup=main_menu)

# --- 16. Bot ishga tushishi ---
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
