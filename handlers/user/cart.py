import logging
from data import config
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.inline.products_from_cart import product_markup, product_cb
from aiogram.utils.callback_data import CallbackData
from keyboards.default.markups import *
from aiogram.types.chat import ChatActions
from states import CheckoutState
from loader import dp, db, bot
# Удален import IsUser
from .menu import cart
from handlers.admin.notifications import send_new_order_notification # Добавлен импорт новой функции
from data.config import ADMINS # Изменен импорт на ADMINS
from states.user_mode_state import UserModeState # Добавлен импорт UserModeState


# Обработчик для кнопки '🛒 Корзина' - срабатывает только в состоянии USER
@dp.message_handler(text=cart, state=UserModeState.USER)
async def process_cart(message: Message, state: FSMContext):

    cart_data = db.fetchall(
        'SELECT * FROM cart WHERE cid=?', (message.chat.id,))

    if len(cart_data) == 0:

        await message.answer('Ваша корзина пуста.')

    else:

        await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
        async with state.proxy() as data:
            data['products'] = {}

        order_cost = 0

        for _, idx, count_in_cart in cart_data:

            product = db.fetchone('SELECT * FROM products WHERE idx=?', (idx,))

            if product == None:

                db.query('DELETE FROM cart WHERE idx=?', (idx,))

            else:
                _, title, body, image, price, _ = product
                order_cost += price

                async with state.proxy() as data:
                    data['products'][idx] = [title, price, count_in_cart]

                markup = product_markup(idx, count_in_cart)
                text = f"""<b>{title}</b>

{body}

Цена: {price}₽."""

                await message.answer_photo(photo=image,
                                           caption=text,
                                           reply_markup=markup)

        if order_cost != 0:
            markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
            markup.add('📦 Оформить заказ')

            await message.answer('Перейти к оформлению?',
                                 reply_markup=markup)


# Обработчики для колбэков товаров в корзине - срабатывают только в состоянии USER
@dp.callback_query_handler(product_cb.filter(action='count'), state=UserModeState.USER)
@dp.callback_query_handler(product_cb.filter(action='increase'), state=UserModeState.USER)
@dp.callback_query_handler(product_cb.filter(action='decrease'), state=UserModeState.USER)
async def product_callback_handler(query: CallbackQuery, callback_data: dict, state: FSMContext):

    idx = callback_data['id']
    action = callback_data['action']

    if 'count' == action:

        async with state.proxy() as data:

            if 'products' not in data.keys():

                await process_cart(query.message, state)

            else:

                await query.answer('Количество - ' + data['products'][idx][2])

    else:

        async with state.proxy() as data:

            if 'products' not in data.keys():

                await process_cart(query.message, state)

            else:

                data['products'][idx][2] += 1 if 'increase' == action else -1
                count_in_cart = data['products'][idx][2]

                if count_in_cart == 0:

                    db.query('''DELETE FROM cart
                    WHERE cid = ? AND idx = ?''', (query.message.chat.id, idx))

                    await query.message.delete()
                else:

                    db.query('''UPDATE cart 
                    SET quantity = ? 
                    WHERE cid = ? AND idx = ?''', (count_in_cart, query.message.chat.id, idx))

                    await query.message.edit_reply_markup(product_markup(idx, count_in_cart))


# Обработчик для кнопки '📦 Оформить заказ' - срабатывает только в состоянии USER
@dp.message_handler(text='📦 Оформить заказ', state=UserModeState.USER)
async def process_checkout(message: Message, state: FSMContext):

    await CheckoutState.check_cart.set()
    await checkout(message, state)


async def checkout(message, state):
    answer = ''
    total_price = 0

    async with state.proxy() as data:

        for title, price, count_in_cart in data['products'].values():

            tp = count_in_cart * price
            answer += f'<b>{title}</b> * {count_in_cart}шт. = {tp}₽'
            total_price += tp

    await message.answer(f'{answer}Общая сумма заказа: {total_price}₽.',
                         reply_markup=check_markup())


# Обработчик для неверного ввода на этапе check_cart - срабатывает только в состоянии check_cart
@dp.message_handler(lambda message: message.text not in [all_right_message, back_message], state=CheckoutState.check_cart)
async def process_check_cart_invalid(message: Message, state: FSMContext): # Добавлен state
    await message.reply('Такого варианта не было.')


# Обработчик для кнопки back на этапе check_cart - срабатывает только в состоянии check_cart
@dp.message_handler(text=back_message, state=CheckoutState.check_cart)
async def process_check_cart_back(message: Message, state: FSMContext):
    await state.finish()
    # После выхода из состояний CheckoutState, пользователь должен вернуться в основное состояние USER
    await UserModeState.USER.set()
    await process_cart(message, state)


# Обработчик для кнопки all_right на этапе check_cart - срабатывает только в состоянии check_cart
@dp.message_handler(text=all_right_message, state=CheckoutState.check_cart)
async def process_check_cart_all_right(message: Message, state: FSMContext):
    await CheckoutState.next()
    await message.answer('Укажите свое имя.',
                         reply_markup=back_markup())


# Обработчик для кнопки back на этапе name - срабатывает только в состоянии name
@dp.message_handler(text=back_message, state=CheckoutState.name)
async def process_name_back(message: Message, state: FSMContext):
    await CheckoutState.check_cart.set()
    await checkout(message, state)


# Обработчик для ввода имени - срабатывает только в состоянии name
@dp.message_handler(state=CheckoutState.name)
async def process_name(message: Message, state: FSMContext):

    async with state.proxy() as data:

        data['name'] = message.text

        if 'address' in data.keys():

            await confirm(message)
            await CheckoutState.confirm.set()

        else:

            await CheckoutState.next()
            await message.answer('Укажите свой адрес места жительства.',
                                 reply_markup=back_markup())


# Обработчик для кнопки back на этапе address - срабатывает только в состоянии address
@dp.message_handler(text=back_message, state=CheckoutState.address)
async def process_address_back(message: Message, state: FSMContext):

    async with state.proxy() as data:

        await message.answer('Изменить имя с <b>' + data['name'] + '</b>?',
                             reply_markup=back_markup())

    await CheckoutState.name.set()


# Обработчик для ввода адреса - срабатывает только в состоянии address
@dp.message_handler(state=CheckoutState.address)
async def process_address(message: Message, state: FSMContext):

    async with state.proxy() as data:
        data['address'] = message.text

    await confirm(message)
    await CheckoutState.next()


async def confirm(message):

    await message.answer('Убедитесь, что все правильно оформлено и подтвердите заказ.',
                         reply_markup=confirm_markup())


# Обработчик для неверного ввода на этапе confirm - срабатывает только в состоянии confirm
@dp.message_handler(lambda message: message.text not in [confirm_message, back_message], state=CheckoutState.confirm)
async def process_confirm_invalid(message: Message, state: FSMContext): # Добавлен state
    await message.reply('Такого варианта не было.')


# Обработчик для кнопки back на этапе confirm - срабатыatолько в состоянии confirm
@dp.message_handler(text=back_message, state=CheckoutState.confirm)
async def process_confirm_back(message: Message, state: FSMContext): # Переименован для уникальности

    await CheckoutState.address.set()

    async with state.proxy() as data:
        await message.answer('Изменить адрес с <b>' + data['address'] + '</b>?',
                             reply_markup=back_markup())


# Обработчик для кнопки confirm на этапе confirm - срабатывает только в состоянии confirm
@dp.message_handler(text=confirm_message, state=CheckoutState.confirm)
async def process_confirm(message: Message, state: FSMContext):

    enough_money = True  # enough money on the balance sheet
    markup = ReplyKeyboardRemove()

    if enough_money:

        logging.info('Deal was made.')

        async with state.proxy() as data:

            cid = message.chat.id
            products = [idx + '=' + str(quantity)
                        for idx, quantity in db.fetchall('''SELECT idx, quantity FROM cart
            WHERE cid=?''', (cid,))]  # idx=quantity

            # Явно указываем столбцы и добавляем значение для status
            db.query('INSERT INTO orders (cid, usr_name, usr_address, products, status) VALUES (?, ?, ?, ?, ?)',
                    (cid, data['name'], data['address'], ' '.join(products), 'новый')) # Добавляем 'новый' как значение для status

            # Получаем ID нового заказа
            order_id = db.get_last_row_id()

            # --- Отправляем сообщение администратору с помощью новой функции ---
            # Используем список ADMINS из data/config.py
            await send_new_order_notification(bot, ADMINS, order_id, cid, data['name'], data['address'], products)
            # -----------------------------------------------------------------

            db.query('DELETE FROM cart WHERE cid=?', (cid,))

            await message.answer('Ок! Ваш заказ уже в пути 🚀Имя: <b>' + data['name'] + '</b>Адрес: <b>' + data['address'] + '</b>',
                                 reply_markup=markup)
    else:

        await message.answer('У вас недостаточно денег на счете. Пополните баланс!',
                             reply_markup=markup)

    await state.finish()
    # После завершения оформления заказа, пользователь должен вернуться в основное состояние USER
    await UserModeState.USER.set()
