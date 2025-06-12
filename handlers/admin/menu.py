from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from loader import db, bot
from states.user_mode_state import UserModeState
from keyboards.inline.categories import CategoryCallbackFactory # Обновленный импорт
from keyboards.default.markups import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

# --- Тексты для кнопок админ-панели ---
SETTINGS_TEXT = '⚙️ Настройки каталога'
ORDERS_TEXT = '📈 Заказы'
NOTIFICATIONS_TEXT = '🔔 Уведомления'
QUESTIONS_TEXT = '❓ Вопросы'


@router.message(F.text == SETTINGS_TEXT, UserModeState.ADMIN)
async def process_settings(message: types.Message, state: FSMContext):
    """
    Показывает настройки категорий и товаров.
    """
    # Создаем клавиатуру с категориями
    categories = db.fetchall('SELECT * FROM categories')
    buttons = [
        [InlineKeyboardButton(
            text=title,
            callback_data=CategoryCallbackFactory(id=idx, action='view').pack()
        )] for idx, title in categories
    ]
    # Добавляем кнопку "Добавить категорию"
    buttons.append([
        InlineKeyboardButton(
            text='+ Добавить категорию',
            callback_data='add_category' # Просто строка, обработаем ее в add.py
        )
    ])
    
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer('Настройка категорий:', reply_markup=markup)

# Другие обработчики меню (заглушки)
@router.message(F.text == ORDERS_TEXT, UserModeState.ADMIN)
async def process_orders(message: types.Message):
    await message.answer('Раздел "Заказы" еще в разработке.')

@router.message(F.text == NOTIFICATIONS_TEXT, UserModeState.ADMIN)
async def process_notifications(message: types.Message):
    await message.answer('Раздел "Уведомления" еще в разработке.')

@router.message(F.text == QUESTIONS_TEXT, UserModeState.ADMIN)
async def process_questions(message: types.Message):
    await message.answer('Раздел "Вопросы" еще в разработке.')
