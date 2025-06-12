from aiogram.types import Message
from aiogram.dispatcher import FSMContext
from loader import dp, db, bot
from data.config import ADMINS
from states.user_mode_state import UserModeState
from handlers.admin.menu import admin_menu
from handlers.user.menu import user_menu

@dp.message_handler(commands=['start'], state='*')
async def start_handler(message: Message, state: FSMContext):
    """
    Центральный обработчик команды /start.
    Определяет роль пользователя и вызывает соответствующее меню.
    """
    # Получаем ID как число (integer)
    cid = message.from_user.id 
    
    # Преобразуем cid в строку только для операций с базой данных
    cid_str = str(cid)

    # Проверяем, существует ли пользователь в базе данных, и если нет - добавляем
    if not db.fetchone('SELECT * FROM cart WHERE cid=?', (cid_str,)):
        db.query('INSERT INTO cart (cid) VALUES (?)', (cid_str,))

    # Сравниваем ЧИСЛО с ЧИСЛАМИ в списке ADMINS
    if cid in ADMINS:
        await state.set_state(UserModeState.ADMIN)
        await admin_menu(message, state)
    else:
        await state.set_state(UserModeState.USER)
        await user_menu(message, state)
