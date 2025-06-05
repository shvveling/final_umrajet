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
    waiting_service = State()
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
        await message.answer("Iltimos, xizmatlardan birini tanlang.", reply_markup=main_menu_kb)
        return

    await state.update_data(service_key=service_key)
    service = services_info[service_key]

    msg_text = (
        f"💠 *{service['name']}*\n\n"
        f"{service['description']}\n\n"
        f"📞 Boshqaruvchilar:\n{get_managers_text(service['managers'])}\n\n"
        "Buyurtma berishni davom ettirish uchun \"✅ Buyurtma berish\" tugmasini bosing yoki 🔙 Orqaga tugmasi bilan bosh menyuga qayting."
    )
    order_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    order_kb.add("✅ Buyurtma berish", "🔙 Orqaga")

    await message.answer(msg_text, reply_markup=order_kb)
    await OrderStates.waiting_order_confirm.set()

# Buyurtmani tasdiqlash
@dp.message_handler(state=OrderStates.waiting_order_confirm)
async def order_confirm_handler(message: types.Message, state: FSMContext):
    if message.text == "✅ Buyurtma berish":
        payment_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        payment_kb.add("💳 Uzcard", "💳 Humo", "💳 Visa", "🪙 Crypto", "🔙 Orqaga")
        await message.answer("Iltimos, to‘lov usulini tanlang:", reply_markup=payment_kb)
        await OrderStates.waiting_payment_method.set()
    elif message.text == "🔙 Orqaga":
        await start_menu(message, state)
    else:
        await message.answer("Iltimos, yuqoridagi tugmalardan birini tanlang.")

# To‘lov usulini tanlash
@dp.message_handler(state=OrderStates.waiting_payment_method)
async def payment_method_handler(message: types.Message, state: FSMContext):
    if is_back_or_cancel(message):
        await start_menu(message, state)
        return

    if message.text not in payment_details.keys():
        await message.answer("Iltimos, to‘lov usullaridan birini tanlang.", reply_markup=payment_kb)
        return

    await state.update_data(payment_method=message.text)
    await message.answer(payment_details[message.text], reply_markup=back_cancel_kb)
    await message.answer("To‘lovni amalga oshiring va tasdiqlovchi hujjatni yuboring (skrinshot, kvitansiya va hokazo).")
    await OrderStates.waiting_payment_proof.set()

# To‘lov tasdiqlovchi hujjatini qabul qilish
@dp.message_handler(state=OrderStates.waiting_payment_proof, content_types=types.ContentTypes.ANY)
async def payment_proof_handler(message: types.Message, state: FSMContext):
    if is_back_or_cancel(message):
        await start_menu(message, state)
        return

    # To‘lov hujjatini qabul qildik deb faraz qilamiz
    data = await state.get_data()
    service_key = data.get("service_key")
    payment_method = data.get("payment_method")

    if not service_key or not payment_method:
        await message.answer("Xatolik yuz berdi. Iltimos, boshidan boshlang.", reply_markup=main_menu_kb)
        await state.finish()
        return

    service = services_info.get(service_key)
    if not service:
        await message.answer("Xizmat topilmadi. Iltimos, boshidan boshlang.", reply_markup=main_menu_kb)
        await state.finish()
        return

    # Adminlarga xabar yuborish
    msg = (
        f"📥 Yangi buyurtma qabul qilindi!\n\n"
        f"Xizmat: *{service['name']}*\n"
        f"To‘lov usuli: *{payment_method}*\n"
        f"Foydalanuvchi: @{message.from_user.username or message.from_user.full_name} (ID: {message.from_user.id})"
    )

    # Adminlarga xabar yuboramiz va to‘lov hujjatini fayl sifatida yuboramiz
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, msg)
            if message.content_type == "photo":
                await bot.send_photo(admin_id, photo=message.photo[-1].file_id, caption="To‘lov tasdiqlovchi rasm")
            elif message.content_type == "document":
                await bot.send_document(admin_id, document=message.document.file_id, caption="To‘lov tasdiqlovchi hujjat")
            elif message.content_type == "video":
                await bot.send_video(admin_id, video=message.video.file_id, caption="To‘lov tasdiqlovchi video")
            else:
                # Agar oddiy matn yoki boshqa turda bo‘lsa, xabarni oddiy matn sifatida yuboramiz
                await bot.send_message(admin_id, f"To‘lov tasdiqlovchi xabar:\n{message.text or 'Nomaʼlum format'}")
        except Exception as e:
            logging.error(f"Adminga xabar yuborishda xatolik: {e}")

    await message.answer("Buyurtmangiz qabul qilindi! Tez orada siz bilan bog‘lanamiz.", reply_markup=main_menu_kb)
    await state.finish()

# Orqaga va bekor qilish tugmalari uchun universal handler
@dp.message_handler(lambda m: m.text in ["🔙 Orqaga", "❌ Bekor qilish"], state="*")
async def back_or_cancel_handler(message: types.Message, state: FSMContext):
    await start_menu(message, state)

# Noma'lum xabarlarni ushlash
@dp.message_handler()
async def unknown_message(message: types.Message):
    await message.answer("Iltimos, menyudan xizmat tanlang yoki /start yozing.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
