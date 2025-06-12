from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# --- Константы для кнопок ---
all_right_message = '✅ Все верно'
cancel_message = '🚫 Отмена'
back_message = '⬅️ Назад'

# --- Клавиатуры для главного меню ---
def user_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='🛍️ Каталог')],
            [KeyboardButton(text='🛒 Корзина'), KeyboardButton(text='🚚 Статус доставки')],
            [KeyboardButton(text='❓ SOS')]
        ],
        resize_keyboard=True
    )

def admin_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='⚙️ Настройки каталога')],
            [KeyboardButton(text='📈 Заказы'), KeyboardButton(text='🔔 Уведомления')],
            [KeyboardButton(text='❓ Вопросы')]
        ],
        resize_keyboard=True
    )

# --- Другие клавиатуры ---
def back_markup():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=back_message)]],
        resize_keyboard=True
    )

def check_markup():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=all_right_message)], [KeyboardButton(text=back_message)]],
        resize_keyboard=True
    )

def cancel_markup():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=cancel_message)]],
        resize_keyboard=True
    )
