import logging
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from loader import db

category_cb = CallbackData('category', 'id', 'action')


def categories_markup():

    global category_cb
    
    markup = InlineKeyboardMarkup()
    categories = db.fetchall('SELECT * FROM categories')
    logging.info(f"Categories from DB: {categories}")
    for idx, title in categories:
        markup.add(InlineKeyboardButton(title, callback_data=category_cb.new(id=idx, action='view')))

    return markup
