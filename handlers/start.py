from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from loader import db
from states.user_mode_state import UserModeState
from keyboards.default.markups import user_main_menu, admin_main_menu
from data.config import ADMINS

# Создаем роутер для этого модуля
router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    """
    Обработчик команды /start.
    Определяет роль пользователя (админ или обычный пользователь) и устанавливает состояние.
    """
    # Сначала сбрасываем предыдущее состояние, если оно было
    await state.clear()
    
    user_id = str(message.from_user.id)
    
    # Проверяем, является ли пользователь админом
    if user_id in ADMINS:
        await state.set_state(UserModeState.ADMIN)
        await message.answer(
            'Добро пожаловать! Вы вошли как администратор.',
            reply_markup=admin_main_menu()
        )
    else:
        # Проверяем, существует ли пользователь в базе данных
        if not db.fetchone('SELECT 1 FROM users WHERE cid = ?', (user_id,)):
            # Если нет, добавляем его
            db.query('INSERT INTO users (cid) VALUES (?)', (user_id,))
        
        await state.set_state(UserModeState.USER)
        await message.answer(
            'Добро пожаловать в наш магазин!',
            reply_markup=user_main_menu()
        )
