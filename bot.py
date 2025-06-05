import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

# Load .env variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))  # comma separated
GROUP_ID = int(os.getenv("GROUP_ID"))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

### FSM states for order processing
class OrderStates(StatesGroup):
    choosing_service = State()
    entering_details = State()
    choosing_payment = State()
    confirming_order = State()

# --- Keyboards ---

def main_menu():
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="🕋 Umra Paketlari", callback_data="service_umra"),
        InlineKeyboardButton(text="🛂 Vizalar", callback_data="service_visa"),
    )
    kb.row(
        InlineKeyboardButton(text="🚆 HHR Poyezd Chiptalari", callback_data="service_train"),
        InlineKeyboardButton(text="🕌 Tasrih & Rawdah", callback_data="service_rawdah"),
    )
    kb.row(
        InlineKeyboardButton(text="🚕 Transport", callback_data="service_transport"),
        InlineKeyboardButton(text="🍽️ Guruh Ovqatlari", callback_data="service_food"),
    )
    kb.row(
        InlineKeyboardButton(text="💳 To‘lov Usullari", callback_data="show_payments"),
    )
    return kb.as_markup()

def payment_menu():
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="💳 Uzcard", callback_data="pay_uzcard"),
        InlineKeyboardButton(text="💳 Humo", callback_data="pay_humo"),
    )
    kb.row(
        InlineKeyboardButton(text="💳 Visa", callback_data="pay_visa"),
        InlineKeyboardButton(text="₿ Crypto", callback_data="pay_crypto"),
    )
    kb.row(
        InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_main"),
    )
    return kb.as_markup()

def back_to_services_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_main")]
    ])

# --- Service descriptions ---
SERVICES = {
    "umra": {
        "title": "🕋 Umra Paketlari",
        "description": (
            "🔹 Siz uchun maxsus tayyorlangan Umra paketlari:\n"
            "- Mehmonxona, transport, taom va qo‘shimcha xizmatlar\n"
            "- Har xil muddatlar va narxlar\n\n"
            "Buyurtma berish uchun «Buyurtma berish» tugmasini bosing."
        ),
        "price": "Narxi: 1000$ dan boshlab",
    },
    "visa": {
        "title": "🛂 Vizalar",
        "description": (
            "🔹 Umra va turistik vizalar xizmatlari.\n"
            "Tez va ishonchli hujjat tayyorlash.\n\n"
            "Buyurtma berish uchun «Buyurtma berish» tugmasini bosing."
        ),
        "price": "Narxi: 300$ dan boshlab",
    },
    "train": {
        "title": "🚆 HHR Poyezd Chiptalari",
        "description": (
            "🔹 Madina – Makka, Riyadh – Dammam, Jiddah – Riyadh va boshqa yo‘nalishlar.\n"
            "Oson va tez chiptalar.\n\n"
            "Buyurtma berish uchun «Buyurtma berish» tugmasini bosing."
        ),
        "price": "Narxi: 50$ dan boshlab",
    },
    "rawdah": {
        "title": "🕌 Tasrih & Rawdah",
        "description": (
            "🔹 Rawdahga kirish ruxsatnomalari va tasrih xizmatlari.\n"
            "Barcha ruxsatnomalarni tayyorlash.\n\n"
            "Buyurtma berish uchun «Buyurtma berish» tugmasini bosing."
        ),
        "price": "Narxi: 150$ dan boshlab",
    },
    "transport": {
        "title": "🚕 Transport",
        "description": (
            "🔹 Aeroportdan mehmonxonaga, ziyorat joylariga transferlar.\n"
            "Quyidagi transport xizmatlari mavjud.\n\n"
            "Buyurtma berish uchun «Buyurtma berish» tugmasini bosing."
        ),
        "price": "Narxi: 30$ dan boshlab",
    },
    "food": {
        "title": "🍽️ Guruh Ovqatlari",
        "description": (
            "🔹 Katta guruhlar uchun maxsus ovqatlanish xizmatlari.\n"
            "Turli menyular va variantlar.\n\n"
            "Buyurtma berish uchun «Buyurtma berish» tugmasini bosing."
        ),
        "price": "Narxi: 20$ dan boshlab",
    }
}

# --- Payment details ---
PAYMENTS = {
    "uzcard": (
        "💳 *Uzcard*\n\n"
        "1234 5678 9012 3456\n"
        "Nom: UmraJet Service\n\n"
        "Kartani nusxalash uchun bosib ushlang."
    ),
    "humo": (
        "💳 *Humo*\n\n"
        "6543 2109 8765 4321\n"
        "Nom: UmraJet Service\n\n"
        "Kartani nusxalash uchun bosib ushlang."
    ),
    "visa": (
        "💳 *Visa*\n\n"
        "4111 1111 1111 1111\n"
        "Nom: UmraJet Service\n\n"
        "Kartani nusxalash uchun bosib ushlang."
    ),
    "crypto": (
        "₿ *Crypto*\n\n"
        "Bitcoin: bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh\n"
        "Ethereum: 0x32Be343B94f860124dC4fEe278FDCBD38C102D88\n\n"
        "Xarid uchun yuqoridagi manzillarga yuboring."
    )
}

# --- Start command ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Assalomu alaykum! UmraJet botiga xush kelibsiz.\n\n"
        "Quyidagi menyudan kerakli bo‘limni tanlang 👇",
        reply_markup=main_menu()
    )

# --- Callback query handler ---
@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data

    if data == "back_to_main":
        await state.clear()
        await callback.message.edit_text(
            "Asosiy menyuga qaytdingiz.",
            reply_markup=main_menu()
        )
        await callback.answer()
        return

    # To‘lov usullari ko‘rsatiladi
    if data == "show_payments":
        await callback.message.edit_text(
            "To‘lov usullaridan birini tanlang:",
            reply_markup=payment_menu()
        )
        await callback.answer()
        return

    # To‘lov tafsilotlari
    if data.startswith("pay_"):
        pay_key = data.split("_")[1]
        pay_text = PAYMENTS.get(pay_key)
        if pay_text:
            await callback.message.edit_text(
                pay_text,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="show_payments")]
                    ]
                ),
                parse_mode="Markdown"
            )
        else:
            await callback.answer("To‘lov ma'lumoti topilmadi.", show_alert=True)
        return

    # Xizmatlar ko‘rsatiladi va buyurtma bosqichi boshlanadi
    if data.startswith("service_"):
        service_key = data.split("_")[1]
        service = SERVICES.get(service_key)
        if service:
            text = f"*{service['title']}*\n\n{service['description']}\n\nNarxi: {service['price']}"
            # "Buyurtma berish" tugmasi bilan
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="📩 Buyurtma berish", callback_data=f"order_{service_key}")],
                    [InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_main")]
                ]
            )
            await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
            await callback.answer()
        else:
            await callback.answer("Xizmat topilmadi.", show_alert=True)
        return

    # Buyurtma jarayoni boshlanadi
    if data.startswith("order_"):
        service_key = data.split("_")[1]
        if service_key not in SERVICES:
            await callback.answer("Noto‘g‘ri xizmat tanlandi.", show_alert=True)
            return
        await state.update_data(service=service_key)
        await OrderStates.entering_details.set()
        await callback.message.edit_text(
            f"📩 *{SERVICES[service_key]['title']}* bo‘yicha buyurtma berish.\n\n"
            "Iltimos, buyurtma tafsilotlarini kiriting:\n"
            "- Ismingiz\n"
            "- Telefon raqamingiz\n"
            "- Qo‘shimcha ma'lumot (agar kerak bo‘lsa)",
            parse_mode="Markdown"
        )
        await callback.answer()
        return

# --- Qabul qilingan buyurtma tafsilotlari ---
@dp.message(StateFilter(OrderStates.entering_details))
async def process_order_details(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if len(text) < 10:
        await message.answer("Iltimos, to‘liq ma'lumot kiriting.")
        return
    await state.update_data(details=text)
    await OrderStates.choosing_payment.set()

    # To‘lov usullarini tanlash
    await message.answer(
        "To‘lov usulini tanlang:",
        reply_markup=payment_menu()
    )

# --- To‘lov usulini tanlash ---
@dp.callback_query(StateFilter(OrderStates.choosing_payment))
async def payment_chosen(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data
    if data.startswith("pay_"):
        pay_key = data.split("_")[1]
        if pay_key not in PAYMENTS:
            await callback.answer("Noto‘g‘ri to‘lov usuli.", show_alert=True)
            return
        await state.update_data(payment=pay_key)
        await OrderStates.confirming_order.set()
        data_state = await state.get_data()
        service_key = data_state["service"]
        details = data_state["details"]
        payment = data_state["payment"]

        pay_text = PAYMENTS[payment]

        confirm_text = (
            f"✅ *Buyurtma tafsilotlari:*\n\n"
            f"Xizmat: {SERVICES[service_key]['title']}\n"
            f"Ma'lumotlar:\n{details}\n\n"
            f"To‘lov usuli:\n{pay_text}\n\n"
            f"Buyurtmani tasdiqlaysizmi?"
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Tasdiqlayman ✅", callback_data="confirm_order"),
                    InlineKeyboardButton(text="Bekor qilish ❌", callback_data="cancel_order"),
                ]
            ]
        )
        await callback.message.edit_text(confirm_text, reply_markup=kb, parse_mode="Markdown")
        await callback.answer()
    elif data == "back_to_main":
        await state.clear()
        await callback.message.edit_text("Asosiy menyuga qaytdingiz.", reply_markup=main_menu())
        await callback.answer()
    else:
        await callback.answer()

# --- Buyurtmani tasdiqlash yoki bekor qilish ---
@dp.callback_query(StateFilter(OrderStates.confirming_order))
async def confirm_or_cancel(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data
    if data == "confirm_order":
        data_state = await state.get_data()
        service_key = data_state["service"]
        details = data_state["details"]
        payment = data_state["payment"]

        # Adminlarga yuborish uchun matn
        msg = (
            f"📩 Yangi buyurtma kelib tushdi!\n\n"
            f"Xizmat: {SERVICES[service_key]['title']}\n"
            f"Ma'lumotlar:\n{details}\n"
            f"To‘lov usuli: {payment.capitalize()}\n\n"
            f"Buyurtmachi: @{callback.from_user.username or callback.from_user.full_name} (ID: {callback.from_user.id})"
        )
        # Adminlarga yuborish
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(admin_id, msg)
            except Exception as e:
                logging.error(f"Adminga xabar yuborishda xato: {e}")
        try:
            await bot.send_message(GROUP_ID, msg)
        except Exception as e:
            logging.error(f"Guruhga xabar yuborishda xato: {e}")

        await callback.message.edit_text("✅ Buyurtmangiz qabul qilindi. Tez orada siz bilan bog‘lanamiz.", reply_markup=main_menu())
        await state.clear()
        await callback.answer("Buyurtma qabul qilindi.")
    elif data == "cancel_order":
        await callback.message.edit_text("❌ Buyurtma bekor qilindi.", reply_markup=main_menu())
        await state.clear()
        await callback.answer("Buyurtma bekor qilindi.")
    else:
        await callback.answer()

# --- Handler for unknown messages ---
@dp.message()
async def unknown_message(message: types.Message):
    await message.answer("Iltimos, menyudan xizmatni tanlang yoki /start ni bosing.")

# --- Run bot ---
if __name__ == "__main__":
    import asyncio
    from aiogram import F
    from aiogram import executor

    executor.start_polling(dp, skip_updates=True)
