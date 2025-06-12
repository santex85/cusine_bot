from aiogram.types import Message
from aiogram.dispatcher import FSMContext
from loader import dp, db, bot
from data.config import ADMINS
from states.user_mode_state import UserModeState
from handlers.admin.menu import admin_menu
from handlers.user.menu import user_menu
import logging

@dp.message_handler(commands=['start'], state='*')
async def start_handler(message: Message, state: FSMContext):
    """
    Центральный обработчик команды /start.
    Определяет роль пользователя и вызывает соответствующее меню.
    """
    # Получаем ID как число (integer), НЕ преобразуем в строку
    cid = message.from_user.id 
    logging.info(f"--- START HANDLER ---")
    logging.info(f"Checking User ID (type: {type(cid)}): {cid}")
    
    # Преобразуем cid в строку только для операций с базой данных
    cid_str = str(cid)

    # Проверяем, существует ли пользователь в базе данных, и если нет - добавляем
    if not db.fetchone('SELECT * FROM cart WHERE cid=?', (cid_str,)):
        logging.info(f"User {cid_str} not in DB. Adding to cart table.")
        db.query('INSERT INTO cart (cid) VALUES (?)', (cid_str,))

    # Сравниваем ЧИСЛО с ЧИСЛАМИ в списке ADMINS
    if cid in ADMINS:
        logging.info(f"User {cid} is ADMIN.")
        await state.set_state(UserModeState.ADMIN)
        logging.info(f"State set to ADMIN. Calling admin_menu...")
        await admin_menu(message, state)
    else:
        logging.info(f"User {cid} is a regular USER.")
        await state.set_state(UserModeState.USER)
        logging.info(f"State set to USER. Calling user_menu...")
        await user_menu(message, state)
    
    logging.info(f"--- END START HANDLER ---")
