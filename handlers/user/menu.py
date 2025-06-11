from aiogram.types import Message, ReplyKeyboardMarkup
from aiogram.dispatcher import FSMContext
from loader import dp, bot
from states.user_mode_state import UserModeState

catalog = '🛍️ Каталог'
cart = '🛒 Корзина'
delivery_status = '🚚 Статус заказа'

# Этот обработчик теперь вызывается только из start_handler
# или других обработчиков в пользовательском режиме
@dp.message_handler(commands='menu', state=UserModeState.USER)
async def user_menu(message: Message, state: FSMContext):
    markup = ReplyKeyboardMarkup(selective=True, resize_keyboard=True)
    markup.add(catalog)
    markup.add(cart)
    markup.add(delivery_status)

    await bot.send_message(message.chat.id, 'Меню', reply_markup=markup)
