import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# 🔐 ДАННЫЕ БОТА
TOKEN = "7909330531:AAEVxXCk1PDl8No_vITK9rnwzzl-Hdw1wBQ"
ADMIN_ID = 6733546966  # Ваш Telegram ID

# 🔗 ССЫЛКИ НА КАНАЛЫ
LINKS = {
    "standoff": "https://t.me/+6p8JI_fWJKtlN2My",
    "pubg": "https://t.me/+-kQ-V5shREU0NzEy",
    "minecraft": "https://t.me/+TYFAa1aOfIMzOGEy"
}

# 🎯 СОЗДАЁМ БОТА
bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

# 🔄 СОСТОЯНИЯ FSM
class OrderState(StatesGroup):
    waiting_for_photo = State()
    waiting_for_details = State()

# 📌 ГЛАВНОЕ МЕНЮ
main_menu = InlineKeyboardMarkup(row_width=1)
main_menu.add(InlineKeyboardButton("🛒 Купить модификацию", callback_data="buy_mods"))
main_menu.add(InlineKeyboardButton("ℹ Информация", callback_data="info"))

# 🎮 МЕНЮ ВЫБОРА ИГРЫ
games_menu = InlineKeyboardMarkup(row_width=2)
games_menu.add(
    InlineKeyboardButton("🔫 Standoff 2 – 500 KZT", callback_data="buy_standoff"),
    InlineKeyboardButton("🎯 PUBG – 700 KZT", callback_data="buy_pubg"),
    InlineKeyboardButton("⛏ Minecraft – 300 KZT", callback_data="buy_minecraft")
)
games_menu.add(InlineKeyboardButton("🔙 Назад", callback_data="main_menu"))

# 📢 СТАРТ БОТА
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer(
        "👋 <b>Приветствуем в Everest Shop!</b>\n"
        "🚀 Здесь ты можешь купить <b>модификации на игры</b> по низким ценам.\n\n"
        "🔽 Выберите действие:", reply_markup=main_menu
    )

# 🔥 ОБРАБОТКА КНОПОК
@dp.callback_query_handler(lambda call: call.data == "info")
async def show_info(call: types.CallbackQuery):
    await call.message.edit_text(
        "📢 <b>Everest Shop</b> – магазин модификаций для популярных игр.\n\n"
        "💳 <b>Оплата:</b> Kaspi\n"
        "📩 После покупки вы получите ссылку на закрытый канал.",
        reply_markup=main_menu
    )

@dp.callback_query_handler(lambda call: call.data == "buy_mods")
async def show_games(call: types.CallbackQuery):
    await call.message.edit_text("🎮 <b>Выберите игру для покупки:</b>", reply_markup=games_menu)

@dp.callback_query_handler(lambda call: call.data == "main_menu")
async def back_to_main(call: types.CallbackQuery):
    await call.message.edit_text("🔽 Выберите действие:", reply_markup=main_menu)

@dp.callback_query_handler(lambda call: call.data.startswith("buy_"))
async def buy_game(call: types.CallbackQuery, state: FSMContext):
    game = call.data.split("_")[1]
    await state.update_data(game=game)
    await OrderState.waiting_for_photo.set()

    await call.message.edit_text(
        "💳 <b>Оплата через Kaspi:</b>\n"
        "📌 Переведите сумму на:\n"
        "👉 <code>4400 4302 1312 5971</code>\n\n"
        "📸 <b>Отправьте фото чека сюда.</b>",
        reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="buy_mods"))
    )

# 📩 ПРИЁМ ФОТО ЧЕКА
@dp.message_handler(content_types=['photo'], state=OrderState.waiting_for_photo)
async def receive_check(message: types.Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await OrderState.waiting_for_details.set()
    await message.answer("📌 Теперь отправьте ваши данные в формате:\n\n<b>ФИО</b>\n<b>Telegram @username</b>")

# 📌 ПРИЁМ ФИО И ТЕЛЕГРАМ-НИКА
@dp.message_handler(state=OrderState.waiting_for_details)
async def receive_details(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    photo = user_data.get("photo")
    game = user_data.get("game")

    await state.finish()

    caption = (
        f"📩 <b>Новый платёж на проверку!</b>\n\n"
        f"👤 От: @{message.from_user.username} (ID: {message.from_user.id})\n"
        f"🎮 Игра: <b>{'Standoff 2' if game == 'standoff' else 'PUBG' if game == 'pubg' else 'Minecraft'}</b>\n"
        f"📜 Данные: <b>{message.text}</b>\n"
        "🔎 Проверьте чек и подтвердите выдачу доступа."
    )

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_{message.from_user.id}_{game}"),
        InlineKeyboardButton("❌ Отклонить", callback_data=f"decline_{message.from_user.id}")
    )

    await bot.send_photo(ADMIN_ID, photo, caption=caption, reply_markup=markup)
    await message.answer("📤 <b>Чек и данные отправлены на проверку!</b> Ожидайте подтверждения.")

# ✅ ОБРАБОТКА ПОДТВЕРЖДЕНИЯ
@dp.callback_query_handler(lambda call: call.data.startswith("confirm_"))
async def confirm_payment(call: types.CallbackQuery):
    parts = call.data.split("_")
    user_id = parts[1]
    game = parts[2]

    link = LINKS.get(game, "❌ Ошибка! Свяжитесь с администратором.")

    await bot.send_message(user_id, f"✅ <b>Оплата подтверждена!</b>\n\n📩 Ваша ссылка: {link}")
    await call.message.edit_text("✅ Оплата подтверждена! Ссылка отправлена пользователю.")

# ❌ ОБРАБОТКА ОТКАЗА
@dp.callback_query_handler(lambda call: call.data.startswith("decline_"))
async def decline_payment(call: types.CallbackQuery):
    user_id = call.data.split("_")[1]
    await bot.send_message(user_id, "❌ <b>Оплата отклонена!</b> Проверьте данные и попробуйте снова.")
    await call.message.edit_text("❌ Оплата отклонена. Сообщение отправлено пользователю.")

# 🚀 СТАРТ БОТА
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)