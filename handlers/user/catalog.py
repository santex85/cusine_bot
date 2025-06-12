import logging
from aiogram.types import Message, CallbackQuery
from keyboards.inline.categories import categories_markup, category_cb
from keyboards.inline.products_from_catalog import product_markup, product_cb
from aiogram.utils.callback_data import CallbackData
from aiogram.types.chat import ChatActions
from loader import dp, db, bot
from .menu import catalog
from aiogram.dispatcher import FSMContext
from states.user_mode_state import UserModeState
from aiogram.utils.exceptions import MessageToDeleteNotFound

@dp.message_handler(text=catalog, state=UserModeState.USER)
async def process_catalog(message: Message, state: FSMContext):
    await bot.send_message(message.chat.id, 'Выберите раздел, чтобы вывести список товаров:',
                         reply_markup=categories_markup())

@dp.callback_query_handler(category_cb.filter(action='view'), state=UserModeState.USER)
async def category_callback_handler(query: CallbackQuery, callback_data: dict, state: FSMContext):
    products = db.fetchall('''SELECT * FROM products product
    WHERE product.tag = (SELECT title FROM categories WHERE idx=?) 
    AND product.idx NOT IN (SELECT idx FROM cart WHERE cid = ?)''',
                           (callback_data['id'], query.message.chat.id))
    await bot.answer_callback_query(query.id, 'Все доступные товары.')
    await show_products(query.message, products)

@dp.callback_query_handler(product_cb.filter(action='add'), state=UserModeState.USER)
async def add_product_callback_handler(query: CallbackQuery, callback_data: dict, state: FSMContext):
    db.query('INSERT INTO cart VALUES (?, ?, 1)',
             (query.message.chat.id, callback_data['id']))
    await bot.answer_callback_query(query.id, 'Товар добавлен в корзину!')
    try:
        await bot.delete_message(query.message.chat.id, query.message.message_id)
    except MessageToDeleteNotFound:
        pass

async def show_products(m, products):
    if len(products) == 0:
        await bot.send_message(m.chat.id, 'Здесь ничего нет 😢')
    else:
        await bot.send_chat_action(m.chat.id, ChatActions.TYPING)
        for idx, title, body, image, price, _ in products:
            markup = product_markup(idx, price)
            text = f"""<b>{title}</b>

{body}

Цена: {price}₽."""
            await bot.send_photo(m.chat.id, photo=image,
                                 caption=text,
                                 reply_markup=markup)
