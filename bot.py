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
    logging.error("❌ .env faylidagi maʼlumotlar toʻliq emas! Iltimos, BOT_TOKEN, ADMIN_IDS va GROUP_ID ni toʻliq kiriting.")
    exit()

# Bot va dispatcher yaratish
bot = Bot(token=BOT_TOKEN)
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
        "managers": ["@vip_arabiy", "@V001VB"]
    },
    "visa": {
        "name": "🛂 Visa Xizmatlari",
        "description": (
            "Umra safaringiz uchun *Visa olish* xizmati! 🌐\n\n"
            "🛂 *Turist Visa* — $120 dan\n"
            "🕋 *Umra Visa* — $160 dan\n\n"
            "Siz uchun barcha rasmiyatchiliklar va hujjatlarni tez va ishonchli hal qilamiz."
        ),
        "managers": ["@vip_arabiy", "@V001VB"]
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
        "managers": ["@vip_arabiy", "@V001VB"]
    },
    "transport": {
        "name": "🚗 Transport Xizmatlari",
        "description": (
            "Safaringiz davomida qulay va xavfsiz transport xizmatlari:\n\n"
            "🚌 Avtobuslar, 🚖 Taksi, 🚐 VIP transport xizmatlari\n"
            "Narxlar va yo‘nalishlar bo‘yicha *managersiz bilan aloqaga chiqing*."
        ),
        "managers": ["@vip_arabiy", "@V001VB"]
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
        "managers": ["@vip_arabiy", "@V001VB"]
    },
    "avia": {
        "name": "✈️ Aviabiletlar",
        "description": (
            "Dunyo bo‘ylab barcha yo‘nalishlarga aviachipta xarid qilish imkoniyati:\n\n"
            "🛫 Siz tanlagan sana va yo‘nalishga moslashgan narxlar\n"
            "🔎 To‘liq xizmat va maslahatlar uchun managerlarga murojaat qiling."
        ),
        "managers": ["@vip_arabiy", "@V001VB"]
    },
    "food": {
        "name": "🍽️ Guruh Ovqatlar",
        "description": (
            "Guruhlar uchun maxsus milliy va xalqaro taomlar:\n\n"
            "🥗 Sifatli, mazali, sog‘lom ovqatlar\n"
            "📞 Narxlar va menyu haqida batafsil ma’lumot uchun managerlarga murojaat qiling."
        ),
        "managers": ["@vip_arabiy", "@V001VB"]
    },
}

# To‘lov ma'lumotlari - aniq, kopiya qilishga qulay, chiroyli
payment_details = {
    "Uzcard": (
        "💳 *Uzcard* orqali to‘lov:\n\n"
        "1️⃣ 8600 0304 9680 2624\n   Khamidov Ibodulloh\n"
        "2️⃣ 5614 6822 1222 3368\n   Khamidov Ibodulloh\n\n"
        "Pul o‘tkazmasini amalga oshirgach, kvitansiyani ilova qiling."
    ),
    "Humo": (
        "💳 *Humo* kartasi:\n\n"
        "9860 1001 2621 9243\n"
        "Khamidov Ibodulloh\n\n"
        "To‘lov qilinganidan so‘ng, kvitansiyani ilova qiling."
    ),
    "Visa": (
        "💳 *Visa* kartalari:\n\n"
        "1️⃣ 4140 8400 0184 8680\n   Khamidov Ibodulloh\n"
        "2️⃣ 4278 3100 2389 5840\n   Khamidov Ibodulloh\n\n"
        "To‘lovni amalga oshiring va kvitansiyani yuboring."
    ),
    "Crypto": (
        "🪙 *Kripto pul o‘tkazmalari* uchun:\n\n"
        "🔹 USDT (TRC20):\n`TLGiUsNzQ8n31x3VwsYiWEU97jdftTDqT3`\n\n"
        "🔹 ETH (BEP20):\n`0xa11fb72cc1ee74cfdaadb25ab2530dd32bafa8f8`\n\n"
        "🔹 BTC (BEP20):\n`0x9A8b67509d176c13a2b5da7e62f1ca1888e55e24`\n\n"
        "To‘lovdan keyin skrinshotni yuboring, tasdiqlaymiz."
    )
}

# Yordamchi funksiya: managerlarni matnga joylash
def get_managers_text(managers):
    return "\n".join([f"👤 @{m}" for m in managers])

# Orqaga / bekor qilish tugmasini tekshirish
def is_back_or_cancel(text):
    return text in ["🔙 Orqaga", "❌ Bekor qilish"]

# --- Handlerlar ---

@dp.message_handler(commands=["start", "help"])
async def cmd_start(message: types.Message):
    text = (
        "Assalomu alaykum! 👋\n\n"
        "Sizni UmraJet botda ko‘rganimizdan xursandmiz! 🤲\n\n"
        "Quyidagi xizmatlardan birini tanlang va buyurtma berish jarayonini boshlang.\n\n"
        "Rasmiy kanallarimiz: @umrajet va @the_ravza"
    )
    await message.answer(text, reply_markup=main_menu_kb)

@dp.message_handler(lambda m: m.text in main_menu_kb.keyboard[0] + main_menu_kb.keyboard[1])
async def service_select_handler(message: types.Message, state: FSMContext):
    text = message.text

    # Qaysi xizmat tanlandi aniqlash
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

    # Xizmat ta'rifi va managerlar ko'rsatiladi
    msg_text = f"💠 *{service['name']}*\n\n{service['description']}\n\n"
    msg_text += "📞 Boshqaruvchilar:\n" + get_managers_text(service["managers"])
    msg_text += "\n\nBuyurtma berishni davom ettirish uchun \"✅ Buyurtma berish\" tugmasini bosing yoki 🔙 Orqaga tugmasi bilan bosh menyuga qayting."

    order_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    order_kb.add("✅ Buyurtma berish", "🔙 Orqaga")

    await message.answer(msg_text, parse_mode="Markdown", reply_markup=order_kb)
    await OrderStates.waiting_order_confirm.set()

@dp.message_handler(lambda m: m.text == "🔙 Orqaga", state="*")
async def go_back_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Asosiy menyuga qaytdingiz.", reply_markup=main_menu_kb)

@dp.message_handler(lambda m: m.text == "❌ Bekor qilish", state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Buyurtma bekor qilindi. Yana xizmatlarimizdan foydalaning!", reply_markup=main_menu_kb)

@dp.message_handler(lambda m: m.text == "✅ Buyurtma berish", state=OrderStates.waiting_order_confirm)
async def order_confirm_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    service_key = data.get("service_key")

    if not service_key or service_key not in services_info:
        await message.answer("Xatolik yuz berdi. Iltimos, qayta urinib ko‘ring.", reply_markup=main_menu_kb)
        await state.finish()
        return

    # To'lov usullari tanlash uchun panel
    await message.answer(
        "To‘lov usulini tanlang. To‘lov maʼlumotlari keyin ko‘rsatiladi.",
        reply_markup=payment_kb
    )
    await OrderStates.waiting_payment_method.set()

@dp.message_handler(lambda m: m.text in payment_details.keys(), state=OrderStates.waiting_payment_method)
async def payment_method_handler(message: types.Message, state: FSMContext):
    pay_method = message.text
    pay_info = payment_details.get(pay_method)

    if not pay_info:
        await message.answer("Iltimos, to‘lov usulini tanlang.", reply_markup=payment_kb)
        return

    # To'lov ma'lumotlarini yuborish
    await message.answer(pay_info, parse_mode="Markdown")

    # Qaytadan skrinshot kutish
    await message.answer(
        "To‘lovni amalga oshirib, kvitansiyani ilova qiling yoki rasm yuboring. "
        "Bekor qilish uchun ❌ Bekor qilish tugmasini bosing.",
        reply_markup=back_cancel_kb
    )
    await state.update_data(payment_method=pay_method)
    await OrderStates.waiting_payment_proof.set()

@dp.message_handler(state=OrderStates.waiting_payment_proof, content_types=types.ContentTypes.ANY)
async def payment_proof_handler(message: types.Message, state: FSMContext):
    if is_back_or_cancel(message.text):
        await go_back_handler(message, state)
        return

    # Skritshot yoki to'lov haqida ma'lumot keladi (matn yoki rasm)
    data = await state.get_data()
    service_key = data.get("service_key")
    payment_method = data.get("payment_method")

    # Buyurtma haqida ma'lumot
    service = services_info.get(service_key)
    managers = service["managers"] if service else []
    managers_mentions = " ".join([f"@{m}" for m in managers])

    # Buyurtma matni tayyorlash
    order_text = (
        f"📢 Yangi buyurtma!\n\n"
        f"Xizmat: {service['name'] if service else 'Noma\'lum'}\n"
        f"To‘lov usuli: {payment_method}\n"
        f"Foydalanuvchi: {message.from_user.full_name} (@{message.from_user.username if message.from_user.username else 'username yo‘q'})\n"
        f"User ID: {message.from_user.id}\n\n"
        f"Managerlarga: {managers_mentions}\n\n"
        f"🔔 To‘lov kvitansiyasi yuborildi."
    )

    # Adminlarga xabar yuborish (matn va kvitansiya rasm bilan)
    for admin_id in ADMIN_IDS:
        try:
            if message.content_type == "photo":
                await bot.send_photo(admin_id, photo=message.photo[-1].file_id, caption=order_text)
            elif message.content_type == "document":
                await bot.send_document(admin_id, document=message.document.file_id, caption=order_text)
            elif message.content_type == "video":
                await bot.send_video(admin_id, video=message.video.file_id, caption=order_text)
            else:
                await bot.send_message(admin_id, order_text)
        except Exception as e:
            logging.error(f"Adminga yuborishda xatolik: {e}")

    # Guruhga xabar yuborish
    try:
        if message.content_type == "photo":
            await bot.send_photo(GROUP_ID, photo=message.photo[-1].file_id, caption=order_text)
        elif message.content_type == "document":
            await bot.send_document(GROUP_ID, document=message.document.file_id, caption=order_text)
        elif message.content_type == "video":
            await bot.send_video(GROUP_ID, video=message.video.file_id, caption=order_text)
        else:
            await bot.send_message(GROUP_ID, order_text)
    except Exception as e:
        logging.error(f"Guruhga yuborishda xatolik: {e}")

    # Foydalanuvchiga tasdiq xabari
    await message.answer(
        "✅ To‘lov kvitansiyasi muvaffaqiyatli qabul qilindi!\n"
        "Tez orada managerlar siz bilan bog‘lanishadi.\n\n"
        "Asosiy menyuga qaytish uchun 🔙 Orqaga tugmasini bosing.",
        reply_markup=main_menu_kb
    )

    await state.finish()

@dp.message_handler()
async def fallback_handler(message: types.Message):
    await message.answer(
        "Iltimos, quyidagi menyudan xizmatni tanlang yoki /start buyrug‘idan foydalaning.",
        reply_markup=main_menu_kb
    )

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
