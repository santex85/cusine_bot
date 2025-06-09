from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ContentType, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.callback_data import CallbackData
from keyboards.default.markups import *
from states import ProductState, CategoryState
from aiogram.types.chat import ChatActions
from handlers.user.menu import settings
from loader import dp, db, bot
# Удален import IsAdmin
from hashlib import md5
from states.user_mode_state import UserModeState # Добавлен импорт UserModeState


category_cb = CallbackData('category', 'id', 'action')
product_cb = CallbackData('product', 'id', 'action')

add_product = '➕ Добавить товар'
delete_category = '🗑️ Удалить категорию'


# Обработчик для кнопки '⚙️ Настройка каталога' - срабатывает только в состоянии ADMIN
@dp.message_handler(text=settings, state=UserModeState.ADMIN) # Изменен фильтр
async def process_settings(message: Message, state: FSMContext): # Добавлен state

    markup = InlineKeyboardMarkup()

    for idx, title in db.fetchall('SELECT * FROM categories'):

        markup.add(InlineKeyboardButton(
            title, callback_data=category_cb.new(id=idx, action='view')))

    markup.add(InlineKeyboardButton(
        '+ Добавить категорию', callback_data='add_category'))

    await message.answer('Настройка категорий:', reply_markup=markup)


# Обработчик для колбэков категорий - срабатывает только в состоянии ADMIN
@dp.callback_query_handler(category_cb.filter(action='view'), state=UserModeState.ADMIN) # Изменен фильтр
async def category_callback_handler(query: CallbackQuery, callback_data: dict, state: FSMContext): # Добавлен state

    category_idx = callback_data['id']

    products = db.fetchall('''SELECT * FROM products product
    WHERE product.tag = (SELECT title FROM categories WHERE idx=?)''',
                           (category_idx,))

    await query.message.delete()
    await query.answer('Все добавленные товары в эту категорию.')
    await state.update_data(category_index=category_idx)
    # Передаем state в show_products если он там нужен, иначе не обязательно
    await show_products(query.message, products, category_idx)


# category


# Обработчик для колбэка 'add_category' - срабатывает только в состоянии ADMIN
@dp.callback_query_handler(text='add_category', state=UserModeState.ADMIN) # Изменен фильтр
async def add_category_callback_handler(query: CallbackQuery, state: FSMContext): # Добавлен state
    await query.message.delete()
    await query.message.answer('Название категории?')
    await CategoryState.title.set()


# Обработчик для установки названия категории - срабатывает только в состоянии CategoryState.title
# Не требует дополнительного фильтра по UserModeState, так как уже в специфическом состоянии
@dp.message_handler(state=CategoryState.title)
async def set_category_title_handler(message: Message, state: FSMContext):

    category = message.text
    idx = md5(category.encode('utf-8')).hexdigest()
    db.query('INSERT INTO categories VALUES (?, ?)', (idx, category))

    await state.finish()
    # После завершения, пользователь должен вернуться в основное состояние ADMIN
    await UserModeState.ADMIN.set()
    await process_settings(message, state) # Передаем state


# Обработчик для кнопки '🗑️ Удалить категорию' - срабатывает только в состоянии ADMIN
@dp.message_handler(text=delete_category, state=UserModeState.ADMIN) # Изменен фильтр
async def delete_category_handler(message: Message, state: FSMContext): # Добавлен state

    async with state.proxy() as data:

        if 'category_index' in data.keys():

            idx = data['category_index']

            db.query(
                'DELETE FROM products WHERE tag IN (SELECT title FROM categories WHERE idx=?)', (idx,))
            db.query('DELETE FROM categories WHERE idx=?', (idx,))

            await message.answer('Готово!', reply_markup=ReplyKeyboardRemove())
            # После завершения, пользователь должен вернуться в основное состояние ADMIN
            await UserModeState.ADMIN.set()
            await process_settings(message, state) # Передаем state


# add product


# Обработчик для кнопки '➕ Добавить товар' - срабатывает только в состоянии ADMIN
@dp.message_handler(text=add_product, state=UserModeState.ADMIN) # Изменен фильтр
async def process_add_product(message: Message, state: FSMContext): # Добавлен state

    await ProductState.title.set()

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(cancel_message)

    await message.answer('Название?', reply_markup=markup)


# Обработчик отмены на этапе title - срабатывает только в состоянии ProductState.title
# Не требует дополнительного фильтра по UserModeState
@dp.message_handler(text=cancel_message, state=ProductState.title)
async def process_cancel(message: Message, state: FSMContext):

    await message.answer('Ок, отменено!', reply_markup=ReplyKeyboardRemove())
    await state.finish()

    # После отмены, пользователь должен вернуться в основное состояние ADMIN
    await UserModeState.ADMIN.set()
    await process_settings(message, state) # Передаем state


# Обработчик кнопки назад на этапе title - срабатывает только в состоянии ProductState.title
# Не требует дополнительного фильтра по UserModeState
@dp.message_handler(text=back_message, state=ProductState.title)
async def process_title_back(message: Message, state: FSMContext): # Добавлен state
    # Возвращаемся к предыдущему шагу (выбор добавления/удаления товара в категории) в состоянии ADMIN
    await UserModeState.ADMIN.set() # Возвращаемся в основное админское состояние
    await process_settings(message, state) # Передаем state


# Обработчик ввода названия товара - срабатывает только в состоянии ProductState.title
# Не требует дополнительного фильтра по UserModeState
@dp.message_handler(state=ProductState.title)
async def process_title(message: Message, state: FSMContext):

    async with state.proxy() as data:
        data['title'] = message.text

    await ProductState.next()
    await message.answer('Описание?', reply_markup=back_markup())


# Обработчик кнопки назад на этапе body - срабатывает только в состоянии ProductState.body
# Не требует дополнительного фильтра по UserModeState
@dp.message_handler(text=back_message, state=ProductState.body)
async def process_body_back(message: Message, state: FSMContext):

    await ProductState.title.set()

    async with state.proxy() as data:

        await message.answer(f"Изменить название с <b>{data['title']}</b>?", reply_markup=back_markup())


# Обработчик ввода описания товара - срабатывает только в состоянии ProductState.body
# Не требует дополнительного фильтра по UserModeState
@dp.message_handler(state=ProductState.body)
async def process_body(message: Message, state: FSMContext):

    async with state.proxy() as data:
        data['body'] = message.text

    await ProductState.next()
    await message.answer('Фото?', reply_markup=back_markup())


# Обработчик загрузки фото - срабатывает только в состоянии ProductState.image
# Не требует дополнительного фильтра по UserModeState
@dp.message_handler(content_types=ContentType.PHOTO, state=ProductState.image)
async def process_image_photo(message: Message, state: FSMContext):

    fileID = message.photo[-1].file_id
    file_info = await bot.get_file(fileID)
    downloaded_file = (await bot.download_file(file_info.file_path)).read()

    async with state.proxy() as data:
        data['image'] = downloaded_file

    await ProductState.next()
    await message.answer('Цена?', reply_markup=back_markup())


# Обработчик текстового ввода на этапе фото (для кнопки назад) - срабатывает только в состоянии ProductState.image
# Не требует дополнительного фильтра по UserModeState
@dp.message_handler(content_types=ContentType.TEXT, state=ProductState.image)
async def process_image_url(message: Message, state: FSMContext):

    if message.text == back_message:

        await ProductState.body.set()

        async with state.proxy() as data:

            await message.answer(f"Изменить описание с <b>{data['body']}</b>?", reply_markup=back_markup())

    else:

        await message.answer('Вам нужно прислать фото товара.')


# Обработчик нечислового ввода цены (включая кнопку назад) - срабатывает только в состоянии ProductState.price
# Не требует дополнительного фильтра по UserModeState
@dp.message_handler(lambda message: not message.text.isdigit(), state=ProductState.price)
async def process_price_invalid(message: Message, state: FSMContext):

    if message.text == back_message:

        await ProductState.image.set()

        async with state.proxy() as data:

            await message.answer("Другое изображение?", reply_markup=back_markup())

    else:

        await message.answer('Укажите цену в виде числа!')


# Обработчик числового ввода цены - срабатывает только в состоянии ProductState.price
# Не требует дополнительного фильтра по UserModeState
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

        await message.answer_photo(photo=data['image'],
                                   caption=text,
                                   reply_markup=markup)


# Обработчик неверного ввода на этапе подтверждения - срабатывает только в состоянии ProductState.confirm
# Не требует дополнительного фильтра по UserModeState
@dp.message_handler(lambda message: message.text not in [back_message, all_right_message], state=ProductState.confirm)
async def process_confirm_invalid(message: Message, state: FSMContext):
    await message.answer('Такого варианта не было.')


# Обработчик кнопки назад на этапе подтверждения - срабатывает только в состоянии ProductState.confirm
# Не требует дополнительного фильтра по UserModeState
@dp.message_handler(text=back_message, state=ProductState.confirm)
async def process_confirm_back(message: Message, state: FSMContext):

    await ProductState.price.set()

    async with state.proxy() as data:

        await message.answer(f"Изменить цену с <b>{data['price']}</b>?", reply_markup=back_markup())


# Обработчик кнопки подтверждения - срабатывает только в состоянии ProductState.confirm
# Не требует дополнительного фильтра по UserModeState
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
    # После завершения, пользователь должен вернуться в основное состояние ADMIN
    await UserModeState.ADMIN.set()
    await message.answer('Готово!', reply_markup=ReplyKeyboardRemove())
    await process_settings(message, state) # Передаем state


# delete product


# Обработчик для колбэка удаления товара - срабатывает только в состоянии ADMIN
@dp.callback_query_handler(product_cb.filter(action='delete'), state=UserModeState.ADMIN) # Изменен фильтр
async def delete_product_callback_handler(query: CallbackQuery, callback_data: dict, state: FSMContext): # Добавлен state

    product_idx = callback_data['id']
    db.query('DELETE FROM products WHERE idx=?', (product_idx,))
    await query.answer('Удалено!')
    await query.message.delete()
    # После удаления, пользователь остается в состоянии ADMIN, нет необходимости сбрасывать состояние UserModeState


# Вспомогательная функция show_products - не обработчик, state здесь не нужен, если он не используется внутри
# Добавлено состояние ADMIN для обработчика ReplyKeyboard
async def show_products(m: Message, products, category_idx):

    await bot.send_chat_action(m.chat.id, ChatActions.TYPING)

    for idx, title, body, image, price, tag in products:

        text = f'<b>{title}</b>{body} Цена: {price} рублей.'

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(
            '🗑️ Удалить', callback_data=product_cb.new(id=idx, action='delete')))

        await m.answer_photo(photo=image,
                             caption=text,
                             reply_markup=markup)

    markup = ReplyKeyboardMarkup()
    markup.add(add_product)
    markup.add(delete_category)

    # Отправляем ReplyKeyboard в состоянии ADMIN
    await m.answer('Хотите что-нибудь добавить или удалить?', reply_markup=markup) # Здесь нет необходимости указывать state
