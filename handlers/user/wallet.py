
from loader import dp
from aiogram.dispatcher import FSMContext
from aiogram.types import Message
# Удален import IsUser
from .menu import balance
from states.user_mode_state import UserModeState # Добавлен импорт UserModeState

# test card ==> 1111 1111 1111 1026, 12/22, CVC 000

# shopId 506751

# shopArticleId 538350

# Обработчик для кнопки '💰 Баланс' - срабатывает только в состоянии USER
@dp.message_handler(text=balance, state=UserModeState.USER) # Изменен фильтр
async def process_balance(message: Message, state: FSMContext):
    await message.answer('Ваш кошелек пуст! Чтобы его пополнить нужно...')

