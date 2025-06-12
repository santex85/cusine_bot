from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

class CatalogProductCallbackFactory(CallbackData, prefix="catalog_product"):
    id: str
    action: str

def product_markup(idx, price):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f'🛒 Добавить в корзину ({price}₽)',
                    callback_data=CatalogProductCallbackFactory(id=idx, action='add').pack()
                )
            ]
        ]
    )
