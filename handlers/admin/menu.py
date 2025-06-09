from aiogram.types import Message, ReplyKeyboardMarkup
from aiogram.dispatcher import FSMContext
from loader import dp
from states.user_mode_state import UserModeState

settings = '⚙️ Настройка каталога'
orders = '🚚 Заказы'
questions = '❓ Вопросы'

@dp.message_handler(commands='menu', state=UserModeState.ADMIN)
async def admin_menu(message: Message, state: FSMContext):
    markup = ReplyKeyboardMarkup(selective=True)
    markup.add(settings)
    markup.add(questions, orders)

    await message.answer('Меню администратора', reply_markup=markup)
