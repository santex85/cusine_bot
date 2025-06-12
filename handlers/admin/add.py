from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ContentType, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.callback_data import CallbackData
from keyboards.default.markups import *
from states import ProductState, CategoryState
from aiogram.types.chat import ChatActions
from handlers.admin.menu import settings
from loader import dp, db, bot
from hashlib import md5
from states.user_mode_state import UserModeState

category_cb = CallbackData('category', 'id', 'action')
product_cb = CallbackData('product', 'id', 'action')

add_product = '➕ Добавить товар'
delete_category = '🗑️ Удалить категорию'

@dp.message_handler(text=settings, state=UserModeState.ADMIN)
async def process_settings(message: Message, state: FSMContext):
    markup = InlineKeyboardMarkup()
    for idx, title in db.fetchall('SELECT * FROM categories'):
        markup.add(InlineKeyboardButton(
            title, callback_data=category_cb.new(id=idx, action='view')))
    markup.add(InlineKeyboardButton(
        '+ Добавить категорию', callback_data='add_category'))
    await bot.send_message(message.chat.id, 'Настройка категорий:', reply_markup=markup)

@dp.callback_query_handler(category_cb.filter(action='view'), state=UserModeState.ADMIN)
async def category_callback_handler(query: CallbackQuery, callback_data: dict, state: FSMContext):
    category_idx = callback_data['id']
    products = db.fetchall('''SELECT * FROM products product
    WHERE product.tag = (SELECT title FROM categories WHERE idx=?)''',
                           (category_idx,))
    await bot.delete_message(query.message.chat.id, query.message.message_id)
    await query.answer('Все добавленные товары в эту категорию.')
    await state.update_data(category_index=category_idx)
    await show_products(query.message, products, category_idx)

@dp.callback_query_handler(text='add_category', state=UserModeState.ADMIN)
async def add_category_callback_handler(query: CallbackQuery, state: FSMContext):
    await bot.delete_message(query.message.chat.id, query.message.message_id)
    await bot.send_message(query.message.chat.id, 'Название категории?')
    await CategoryState.title.set()

@dp.message_handler(state=CategoryState.title)
async def set_category_title_handler(message: Message, state: FSMContext):
    category = message.text
    idx = md5(category.encode('utf-8')).hexdigest()
    db.query('INSERT INTO categories VALUES (?, ?)', (idx, category))
    await state.finish()
    await UserModeState.ADMIN.set()
    await process_settings(message, state)

@dp.message_handler(text=delete_category, state=UserModeState.ADMIN)
async def delete_category_handler(message: Message, state: FSMContext):
    async with state.proxy() as data:
        if 'category_index' in data.keys():
            idx = data['category_index']
            db.query(
                'DELETE FROM products WHERE tag IN (SELECT title FROM categories WHERE idx=?)', (idx,))
            db.query('DELETE FROM categories WHERE idx=?', (idx,))
            await bot.send_message(message.chat.id, 'Готово!', reply_markup=ReplyKeyboardRemove())
            await UserModeState.ADMIN.set()
            await process_settings(message, state)

@dp.message_handler(text=add_product, state=UserModeState.ADMIN)
async def process_add_product(message: Message, state: FSMContext):
    await ProductState.title.set()
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(cancel_message)
    await bot.send_message(message.chat.id, 'Название?', reply_markup=markup)

@dp.message_handler(text=cancel_message, state=ProductState.title)
async def process_cancel(message: Message, state: FSMContext):
    await bot.send_message(message.chat.id, 'Ок, отменено!', reply_markup=ReplyKeyboardRemove())
    await state.finish()
    await UserModeState.ADMIN.set()
    await process_settings(message, state)

@dp.message_handler(text=back_message, state=ProductState.title)
async def process_title_back(message: Message, state: FSMContext):
    await UserModeState.ADMIN.set()
    await process_settings(message, state)

@dp.message_handler(state=ProductState.title)
async def process_title(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['title'] = message.text
    await ProductState.next()
    await bot.send_message(message.chat.id, 'Описание?', reply_markup=back_markup())

@dp.message_handler(text=back_message, state=ProductState.body)
async def process_body_back(message: Message, state: FSMContext):
    await ProductState.title.set()
    async with state.proxy() as data:
        await bot.send_message(message.chat.id, f"Изменить название с <b>{data['title']}</b>?", reply_markup=back_markup())

@dp.message_handler(state=ProductState.body)
async def process_body(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['body'] = message.text
    await ProductState.next()
    await bot.send_message(message.chat.id, 'Фото?', reply_markup=back_markup())

@dp.message_handler(content_types=ContentType.PHOTO, state=ProductState.image)
async def process_image_photo(message: Message, state: FSMContext):
    fileID = message.photo[-1].file_id
    file_info = await bot.get_file(fileID)
    downloaded_file = (await bot.download_file(file_info.file_path)).read()
    async with state.proxy() as data:
        data['image'] = downloaded_file
    await ProductState.next()
    await bot.send_message(message.chat.id, 'Цена?', reply_markup=back_markup())

@dp.message_handler(content_types=ContentType.TEXT, state=ProductState.image)
async def process_image_url(message: Message, state: FSMContext):
    if message.text == back_message:
        await ProductState.body.set()
        async with state.proxy() as data:
            await bot.send_message(message.chat.id, f"Изменить описание с <b>{data['body']}</b>?", reply_markup=back_markup())
    else:
        await bot.send_message(message.chat.id, 'Вам нужно прислать фото товара.')

@dp.message_handler(lambda message: not message.text.isdigit(), state=ProductState.price)
async def process_price_invalid(message: Message, state: FSMContext):
    if message.text == back_message:
        await ProductState.image.set()
        async with state.proxy() as data:
            await bot.send_message(message.chat.id, "Другое изображение?", reply_markup=back_markup())
    else:
        await bot.send_message(message.chat.id, 'Укажите цену в виде числа!')

@dp.message_handler(lambda message: message.text.isdigit(), state=ProductState.price)
async def process_price(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['price'] = message.text
        title = data['title']
        body = data['body']
        price = data['price']
        await ProductState.next()
        text = f'<b>{title}</b>{body}Цена: {price} рублей.'
        markup = check_markup()
        await bot.send_photo(message.chat.id, photo=data['image'],
                                   caption=text,
                                   reply_markup=markup)

@dp.message_handler(lambda message: message.text not in [back_message, all_right_message], state=ProductState.confirm)
async def process_confirm_invalid(message: Message, state: FSMContext):
    await bot.send_message(message.chat.id, 'Такого варианта не было.')

@dp.message_handler(text=back_message, state=ProductState.confirm)
async def process_confirm_back(message: Message, state: FSMContext):
    await ProductState.price.set()
    async with state.proxy() as data:
        await bot.send_message(message.chat.id, f"Изменить цену с <b>{data['price']}</b>?", reply_markup=back_markup())

@dp.message_handler(text=all_right_message, state=ProductState.confirm)
async def process_confirm(message: Message, state: FSMContext):
    async with state.proxy() as data:
        title = data['title']
        body = data['body']
        image = data['image']
        price = data['price']
        tag = db.fetchone(
            'SELECT title FROM categories WHERE idx=?', (data['category_index'],))[0]
        idx = md5(' '.join([title, body, price, tag]
                           ).encode('utf-8')).hexdigest()
        db.query('INSERT INTO products VALUES (?, ?, ?, ?, ?, ?)',
                 (idx, title, body, image, int(price), tag))
    await state.finish()
    await UserModeState.ADMIN.set()
    await bot.send_message(message.chat.id, 'Готово!', reply_markup=ReplyKeyboardRemove())
    await process_settings(message, state)

@dp.callback_query_handler(product_cb.filter(action='delete'), state=UserModeState.ADMIN)
async def delete_product_callback_handler(query: CallbackQuery, callback_data: dict, state: FSMContext):
    product_idx = callback_data['id']
    db.query('DELETE FROM products WHERE idx=?', (product_idx,))
    await query.answer('Удалено!')
    await bot.delete_message(query.message.chat.id, query.message.message_id)

async def show_products(m: Message, products, category_idx):
    await bot.send_chat_action(m.chat.id, ChatActions.TYPING)
    for idx, title, body, image, price, tag in products:
        text = f'<b>{title}</b>{body} Цена: {price} рублей.'
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(
            '🗑️ Удалить', callback_data=product_cb.new(id=idx, action='delete')))
        await bot.send_photo(m.chat.id, photo=image,
                             caption=text,
                             reply_markup=markup)
    markup = ReplyKeyboardMarkup()
    markup.add(add_product)
    markup.add(delete_category)
    await bot.send_message(m.chat.id, 'Хотите что-нибудь добавить или удалить?', reply_markup=markup)
