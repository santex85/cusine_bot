from aiogram.types import Message, ReplyKeyboardMarkup
from aiogram.dispatcher import FSMContext
# Импортируем сам модуль loader
import loader
from states.user_mode_state import UserModeState

catalog = '🛍️ Каталог'
cart = '🛒 Корзина'
delivery_status = '🚚 Статус заказа'

# Используем loader.dp для регистрации обработчика
@loader.dp.message_handler(commands='menu', state=UserModeState.USER)
async def user_menu(message: Message, state: FSMContext):
    markup = ReplyKeyboardMarkup(selective=True, resize_keyboard=True)
    markup.add(catalog)
    markup.add(cart)
    markup.add(delivery_status)

    await message.answer('Меню пользователя', reply_markup=markup)
