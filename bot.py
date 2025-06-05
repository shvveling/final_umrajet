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
ADMIN_IDS = list(map(int, filter(None, os.getenv("ADMIN_IDS", "").split(","))))
GROUP_ID = int(os.getenv("GROUP_ID", "0"))

if not BOT_TOKEN or not ADMIN_IDS or not GROUP_ID:
    logging.error("❌ .env faylidagi maʼlumotlar toʻliq emas! Iltimos, BOT_TOKEN, ADMIN_IDS va GROUP_ID ni toʻliq kiriting.")
    exit()

# Bot va dispatcher yaratish
bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.MARKDOWN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# FSM holatlari
class OrderStates(StatesGroup):
    waiting_order_confirm = State()
    waiting_payment_method = State()
    waiting_payment_proof = State()

# Asosiy menyu tugmalari
main_menu_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
main_menu_kb.add(
    "🕋 Umra Paketlari", "🛂 Visa Xizmatlari",
    "🌙 Ravza Ruxsatnomalari", "🚗 Transport Xizmatlari",
    "🚆 Po‘ezd Biletlar", "✈️ Aviabiletlar",
    "🍽️ Guruh Ovqatlar"
)

# Orqaga va bekor qilish tugmalari
back_cancel_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
back_cancel_kb.add("🔙 Orqaga", "❌ Bekor qilish")

# To‘lov usullari paneli
payment_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
payment_kb.add("💳 Uzcard", "💳 Humo", "💳 Visa", "🪙 Crypto", "🔙 Orqaga")

# Xizmatlar ma'lumotlari - premium, marketingga to'la, sodda va tushunarli
services_info = {
    "umra_paket": {
        "name": "🕋 Umra Paketlari",
        "description": (
            "Sizga mo‘ljallangan *Umra Paketlari* bilan qulay va ishonchli safarga tayyorlaning! 🌟\n\n"
            "✅ *Oddiy Paket* — faqat $1100 dan\n✅ *VIP Paket* — eksklyuziv xizmatlar bilan $2000 dan\n\n"
            "Paketga kiradi:\n"
            "✈️ Parvoz, 🏨 Mehmxonada joylashish, 🚖 Transport xizmatlari\n"
            "🍽️ Guruh ovqatlar, 🤲 Doimiy qo‘llab-quvvatlash"
        ),
        "managers": ["vip_arabiy", "V001VB"]
    },
    "visa": {
        "name": "🛂 Visa Xizmatlari",
        "description": (
            "Umra safaringiz uchun *Visa olish* xizmati! 🌐\n\n"
            "🛂 *Turist Visa* — $120 dan\n"
            "🕋 *Umra Visa* — $160 dan\n\n"
            "Siz uchun barcha rasmiyatchiliklar va hujjatlarni tez va ishonchli hal qilamiz."
        ),
        "managers": ["vip_arabiy", "V001VB"]
    },
    "ravza": {
        "name": "🌙 Ravza Ruxsatnomalari",
        "description": (
            "Ravza tashrifi uchun ruxsatnomalar:\n\n"
            "📌 *Viza mavjud bo‘lsa*: 15 SAR (har bir ruxsatnoma uchun)\n"
            "📌 *Viza mavjud bo‘lmasa*: 20 SAR (har bir ruxsatnoma uchun)\n\n"
            "👥 *Guruh bo‘lib buyurtma qilganlarga maxsus chegirmalar!*\n\n"
            "Ravza tashrifi sizga Allohning muqaddas joyida mehr-oqibatni his qilish uchun imkon yaratadi."
        ),
        "managers": ["vip_arabiy", "V001VB"]
    },
    "transport": {
        "name": "🚗 Transport Xizmatlari",
        "description": (
            "Safaringiz davomida qulay va xavfsiz transport xizmatlari:\n\n"
            "🚌 Avtobuslar, 🚖 Taksi, 🚐 VIP transport xizmatlari\n"
            "Narxlar va yo‘nalishlar bo‘yicha *managerlar bilan aloqaga chiqing*."
        ),
        "managers": ["vip_arabiy", "V001VB"]
    },
    "train": {
        "name": "🚆 Po‘ezd Biletlar",
        "description": (
            "HHR temir yo‘llari orqali qulay po‘ezd chiptalarini taqdim etamiz:\n\n"
            "📍 *Madina – Makka*\n"
            "📍 *Makka – Madina*\n"
            "📍 *Riyadh – Dammam*\n"
            "📍 *Jeddah – Makka*\n\n"
            "Narxlar yo‘nalishlarga ko‘ra farqlanadi. Batafsil ma’lumot uchun managerlar bilan bog‘laning."
        ),
        "managers": ["vip_arabiy", "V001VB"]
    },
    "avia": {
        "name": "✈️ Aviabiletlar",
        "description": (
            "Dunyo bo‘ylab barcha yo‘nalishlarga aviachipta xarid qilish imkoniyati:\n\n"
            "🛫 Siz tanlagan sana va yo‘nalishga moslashgan narxlar\n"
            "🔎 To‘liq xizmat va maslahatlar uchun managerlarga murojaat qiling."
        ),
        "managers": ["vip_arabiy", "V001VB"]
    },
    "food": {
        "name": "🍽️ Guruh Ovqatlar",
        "description": (
            "Guruhlar uchun maxsus milliy va xalqaro taomlar:\n\n"
            "🥗 Sifatli, mazali, sog‘lom ovqatlar\n"
            "📞 Narxlar va menyu haqida batafsil ma’lumot uchun managerlarga murojaat qiling."
        ),
        "managers": ["vip_arabiy", "V001VB"]
    },
}

# To‘lov ma'lumotlari - aniq, kopiya qilishga qulay, chiroyli
payment_details = {
    "💳 Uzcard": (
        "💳 *Uzcard* orqali to‘lov:\n\n"
        "1️⃣ 8600 0304 9680 2624\n   Khamidov Ibodulloh\n"
        "2️⃣ 5614 6822 1222 3368\n   Khamidov Ibodulloh\n\n"
        "Pul o‘tkazmasini amalga oshirgach, kvitansiyani ilova qiling."
    ),
    "💳 Humo": (
        "💳 *Humo* kartasi:\n\n"
        "9860 1001 2621 9243\n"
        "Khamidov Ibodulloh\n\n"
        "To‘lov qilinganidan so‘ng, kvitansiyani ilova qiling."
    ),
    "💳 Visa": (
        "💳 *Visa* kartalari:\n\n"
        "1️⃣ 4205 7100 1133 5486\n   Khamidov Ibodulloh\n"
        "2️⃣ 4205 7100 1312 2302\n   Khamidov Ibodulloh\n\n"
        "To‘lovni amalga oshirib, kvitansiyani yuboring."
    ),
    "🪙 Crypto": (
        "🪙 *Crypto* to‘lovlari:\n\n"
        "Bitcoin (BTC): 1BoatSLRHtKNngkdXEeobR76b53LETtpyT\n"
        "Ethereum (ETH): 0x32Be343B94f860124dC4fEe278FDCBD38C102D88\n\n"
        "To‘lovdan so‘ng, tasdiqlovchi ma’lumotlarni yuboring."
    )
}

# Yordamchi funksiya: managerlarni ko'rsatish uchun
def get_managers_text(usernames):
    return "\n".join([f"@{username}" for username in usernames])

# Yordamchi funksiya: orqaga yoki bekor qilish tugmasi bosilganini tekshirish
def is_back_or_cancel(message: types.Message):
    if not message.text:
        return False
    return message.text in ["🔙 Orqaga", "❌ Bekor qilish"]

# Boshlang‘ich komandasi
@dp.message_handler(commands=["start", "menu"])
async def start_menu(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "Assalomu alaykum! UmraJetBotga xush kelibsiz.\n"
        "Quyidagi xizmatlarimizdan birini tanlang:",
        reply_markup=main_menu_kb
    )

# Xizmat tanlash handleri
@dp.message_handler(lambda m: m.text in sum(main_menu_kb.keyboard, []))
async def service_select_handler(message: types.Message, state: FSMContext):
    text = message.text
    service_key = None
    for key, info in services_info.items():
        if text == info["name"]:
            service_key = key
            break

    if not service_key:
        await message.answer("Iltimos, quyidagi tugmalardan birini tanlang.")
        return

    service = services_info[service_key]
    managers = get_managers_text(service["managers"])
    response = (
        f"<b>{service['name']}</b>\n\n"
        f"{service['description']}\n\n"
        f"📞 <b>Managerlar:</b>\n{managers}\n\n"
        "Buyurtma berish uchun to‘lov usulini tanlang."
    )
    await OrderStates.waiting_payment_method.set()
    await state.update_data(service=service_key)
    await message.answer(response, reply_markup=payment_kb)

# To‘lov usuli tanlash handleri
@dp.message_handler(state=OrderStates.waiting_payment_method)
async def payment_method_handler(message: types.Message, state: FSMContext):
    text = message.text

    if text == "🔙 Orqaga":
        await start_menu(message, state)
        return
    if text == "❌ Bekor qilish":
        await state.finish()
        await message.answer("Buyurtma bekor qilindi. Kerak bo‘lsa, boshidan boshlang.", reply_markup=main_menu_kb)
        return
    if text not in payment_details:
        await message.answer("Iltimos, to‘lov usullaridan birini tanlang.", reply_markup=payment_kb)
        return

    # Tanlangan xizmat va to‘lov usuli saqlanadi
    data = await state.get_data()
    service_key = data.get("service")
    if not service_key:
        await message.answer("Xatolik yuz berdi. Iltimos, boshidan boshlang.", reply_markup=main_menu_kb)
        await state.finish()
        return

    pay_info = payment_details[text]

    await state.update_data(payment_method=text)
    await OrderStates.waiting_payment_proof.set()
    await message.answer(
        f"<b>To‘lov maʼlumotlari ({text}):</b>\n\n"
        f"{pay_info}\n\n"
        "To‘lovni amalga oshirgach, iltimos, to‘lov kvitansiyasining rasmini yoki skrinshotini yuboring.\n\n"
        "Agar bekor qilmoqchi bo‘lsangiz, «❌ Bekor qilish» tugmasini bosing.",
        reply_markup=back_cancel_kb
    )

# To‘lov kvitansiyasi qabul qilish handleri
@dp.message_handler(content_types=types.ContentType.PHOTO, state=OrderStates.waiting_payment_proof)
async def payment_proof_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    service_key = data.get("service")
    payment_method = data.get("payment_method")

    if not service_key or not payment_method:
        await message.answer("Xatolik yuz berdi. Iltimos, boshidan boshlang.", reply_markup=main_menu_kb)
        await state.finish()
        return

    # Adminlarga xabar yuborish
    service = services_info[service_key]
    managers = get_managers_text(service["managers"])

    caption = (
        f"📥 Yangi buyurtma!\n\n"
        f"🕋 Xizmat: <b>{service['name']}</b>\n"
        f"💳 To‘lov usuli: <b>{payment_method}</b>\n"
        f"👤 Foydalanuvchi: {message.from_user.get_mention(as_html=True)}\n"
        f"🆔 User ID: <code>{message.from_user.id}</code>\n\n"
        f"📞 Managerlar: {managers}\n\n"
        f"⏳ Iltimos, buyurtmani tezda ko‘rib chiqing."
    )

    # Rasmi adminlarga yuborish
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_photo(admin_id, photo=message.photo[-1].file_id, caption=caption, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Adminga xabar yuborishda xatolik: {e}")

    # Guruhga ham yuborish (agar GROUP_ID aniq ko‘rsatilgan bo‘lsa)
    if GROUP_ID != 0:
        try:
            await bot.send_photo(GROUP_ID, photo=message.photo[-1].file_id, caption=caption, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Guruhga xabar yuborishda xatolik: {e}")

    await message.answer(
        "To‘lov kvitansiyangiz qabul qilindi! Tez orada managerlarimiz siz bilan bog‘lanishadi.\n\n"
        "Yana xizmatlardan foydalanish uchun bosh menyuga qayting.",
        reply_markup=main_menu_kb
    )
    await state.finish()

# Agar foydalanuvchi rasmdan boshqa narsa yuborsa (to‘lov kvitansiyasi o‘rnida)
@dp.message_handler(state=OrderStates.waiting_payment_proof)
async def invalid_payment_proof_handler(message: types.Message, state: FSMContext):
    if is_back_or_cancel(message):
        if message.text == "🔙 Orqaga":
            data = await state.get_data()
            # To‘lov usuli tanlashga qaytamiz
            await OrderStates.waiting_payment_method.set()
            await message.answer("To‘lov usulini qayta tanlang:", reply_markup=payment_kb)
        else:
            await state.finish()
            await message.answer("Buyurtma bekor qilindi.", reply_markup=main_menu_kb)
        return

    await message.answer(
        "Iltimos, to‘lov kvitansiyasining rasm shaklini yuboring yoki «❌ Bekor qilish» tugmasini bosing."
    )

# Orqaga/ bekor qilish tugmalari har doim ishlashi uchun universal handler (boshqa holatlar uchun)
@dp.message_handler(lambda m: m.text in ["🔙 Orqaga", "❌ Bekor qilish"])
async def back_cancel_global_handler(message: types.Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await start_menu(message, state)
    else:
        await state.finish()
        await message.answer("Buyurtma bekor qilindi.", reply_markup=main_menu_kb)

# Noto‘g‘ri buyruqlar uchun oddiy javob
@dp.message_handler()
async def default_handler(message: types.Message):
    await message.answer(
        "Iltimos, menyudan kerakli xizmatni tanlang yoki /start buyrug‘ini bering.",
        reply_markup=main_menu_kb
    )

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
