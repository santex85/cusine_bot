from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from loader import db

class CategoryCallbackFactory(CallbackData, prefix="category"):
    id: str
    action: str

def categories_markup():
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=title, 
                callback_data=CategoryCallbackFactory(id=idx, action='view').pack()
            )]
            for idx, title in db.fetchall('SELECT * FROM categories')
        ]
    )
    return markup
