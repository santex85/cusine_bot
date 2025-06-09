from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup
from aiogram.dispatcher import FSMContext # Импорт FSMContext
from loader import dp
# Удалены IsAdmin, IsUser
from states.user_mode_state import UserModeState # Импорт состояний режимов пользователя

catalog = '🛍️ Каталог'
balance = '💰 Баланс'
cart = '🛒 Корзина'
delivery_status = '🚚 Статус заказа'

settings = '⚙️ Настройка каталога'
orders = '🚚 Заказы'
questions = '❓ Вопросы'

# Обработчик меню администратора - срабатывает только в состоянии ADMIN
@dp.message_handler(commands='menu', state=UserModeState.ADMIN)
async def admin_menu(message: Message, state: FSMContext): # Добавлен state
    markup = ReplyKeyboardMarkup(selective=True)
    markup.add(settings)
    markup.add(questions, orders)

    await message.answer('Меню администратора', reply_markup=markup)

# Обработчик меню пользователя - срабатывает только в состоянии USER
@dp.message_handler(commands='menu', state=UserModeState.USER)
async def user_menu(message: Message, state: FSMContext): # Добавлен state
    markup = ReplyKeyboardMarkup(selective=True)
    markup.add(catalog)
    markup.add(balance, cart)
    markup.add(delivery_status)

    await message.answer('Меню пользователя', reply_markup=markup)
