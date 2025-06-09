import logging
from aiogram.types import Message, CallbackQuery
from keyboards.inline.categories import categories_markup, category_cb
from keyboards.inline.products_from_catalog import product_markup, product_cb
from aiogram.utils.callback_data import CallbackData
from aiogram.types.chat import ChatActions
from loader import dp, db, bot
from .menu import catalog
# Удален import IsUser
from aiogram.dispatcher import FSMContext # Добавлен импорт FSMContext
from states.user_mode_state import UserModeState # Добавлен импорт UserModeState


# Обработчик для кнопки '🛍️ Каталог' - срабатывает только в состоянии USER
@dp.message_handler(text=catalog, state=UserModeState.USER)
async def process_catalog(message: Message, state: FSMContext): # Добавлен state
    await message.answer('Выберите раздел, чтобы вывести список товаров:',
                         reply_markup=categories_markup())


# Обработчик для колбэков категорий - срабатывает только в состоянии USER
@dp.callback_query_handler(category_cb.filter(action='view'), state=UserModeState.USER) # Изменен фильтр
async def category_callback_handler(query: CallbackQuery, callback_data: dict, state: FSMContext): # Добавлен state

    products = db.fetchall('''SELECT * FROM products product
    WHERE product.tag = (SELECT title FROM categories WHERE idx=?) 
    AND product.idx NOT IN (SELECT idx FROM cart WHERE cid = ?)''',
                           (callback_data['id'], query.message.chat.id))

    await query.answer('Все доступные товары.')
    # Передаем state в show_products если он там нужен, иначе не обязательно
    await show_products(query.message, products)


# Обработчик для колбэков добавления товара - срабатывает только в состоянии USER
@dp.callback_query_handler(product_cb.filter(action='add'), state=UserModeState.USER) # Изменен фильтр
async def add_product_callback_handler(query: CallbackQuery, callback_data: dict, state: FSMContext): # Добавлен state

    db.query('INSERT INTO cart VALUES (?, ?, 1)',
             (query.message.chat.id, callback_data['id']))

    await query.answer('Товар добавлен в корзину!')
    await query.message.delete()


# Вспомогательная функция show_products - не обработчик, state здесь не нужен, если он не используется внутри
async def show_products(m, products):

    if len(products) == 0:

        await m.answer('Здесь ничего нет 😢')

    else:

        await bot.send_chat_action(m.chat.id, ChatActions.TYPING)

        for idx, title, body, image, price, _ in products:

            markup = product_markup(idx, price)
            text = f"""<b>{title}</b>

{body}

Цена: {price}₽."""

            await m.answer_photo(photo=image,
                                 caption=text,
                                 reply_markup=markup)
