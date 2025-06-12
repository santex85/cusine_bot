from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

class CartProductCallbackFactory(CallbackData, prefix="cart_product"):
    id: str
    action: str

def product_markup(idx, count):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='-', callback_data=CartProductCallbackFactory(id=idx, action='decrease').pack()),
                InlineKeyboardButton(text=f'{count} шт.', callback_data='count_ignore'),
                InlineKeyboardButton(text='+', callback_data=CartProductCallbackFactory(id=idx, action='increase').pack()),
            ],
            [
                InlineKeyboardButton(text='🗑️ Удалить', callback_data=CartProductCallbackFactory(id=idx, action='delete').pack())
            ]
        ]
    )
