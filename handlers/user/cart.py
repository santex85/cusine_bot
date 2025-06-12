import logging
from data import config
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.exceptions import MessageNotModified, MessageToDeleteNotFound
from keyboards.inline.products_from_cart import product_markup, product_cb
from aiogram.utils.callback_data import CallbackData
from keyboards.default.markups import *
from aiogram.types.chat import ChatActions
from states import CheckoutState
from loader import dp, db, bot
from .menu import user_menu, cart
from handlers.admin.notifications import send_new_order_notification
from data.config import ADMINS
from states.user_mode_state import UserModeState

@dp.message_handler(text=cart, state=UserModeState.USER)
async def process_cart(message: Message, state: FSMContext):
    cart_data = db.fetchall(
        'SELECT * FROM cart WHERE cid=?', (message.chat.id,))
    if len(cart_data) == 0:
        await bot.send_message(message.chat.id, 'Ваша корзина пуста.')
    else:
        await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
        async with state.proxy() as data:
            data['products'] = {}
        order_cost = 0
        for _, idx, count_in_cart in cart_data:
            product = db.fetchone('SELECT * FROM products WHERE idx=?', (idx,))
            if product is None:
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
                await bot.send_photo(message.chat.id, photo=image,
                                     caption=text,
                                     reply_markup=markup)
        if order_cost != 0:
            markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
            markup.add('📦 Оформить заказ')
            await bot.send_message(message.chat.id, 'Перейти к оформлению?',
                                 reply_markup=markup)

@dp.callback_query_handler(product_cb.filter(action=['count', 'increase', 'decrease']), state=UserModeState.USER)
async def product_callback_handler(query: CallbackQuery, callback_data: dict, state: FSMContext):
    idx = callback_data['id']
    action = callback_data['action']
    if 'count' == action:
        async with state.proxy() as data:
            if 'products' not in data.keys():
                await process_cart(query.message, state)
            else:
                await bot.answer_callback_query(query.id, f"Количество - {data['products'][idx][2]}")
    else:
        async with state.proxy() as data:
            if 'products' not in data.keys():
                await process_cart(query.message, state)
            else:
                data['products'][idx][2] += 1 if 'increase' == action else -1
                count_in_cart = data['products'][idx][2]
                if count_in_cart == 0:
                    db.query('DELETE FROM cart WHERE cid = ? AND idx = ?', (query.message.chat.id, idx))
                    try:
                        await bot.delete_message(query.message.chat.id, query.message.message_id)
                    except MessageToDeleteNotFound:
                        pass
                else:
                    db.query('UPDATE cart SET quantity = ? WHERE cid = ? AND idx = ?', (count_in_cart, query.message.chat.id, idx))
                    try:
                        await bot.edit_message_reply_markup(query.message.chat.id, query.message.message_id, reply_markup=product_markup(idx, count_in_cart))
                    except MessageNotModified:
                        pass

@dp.message_handler(text='📦 Оформить заказ', state=UserModeState.USER)
async def process_checkout(message: Message, state: FSMContext):
    await state.set_state(CheckoutState.check_cart)
    await checkout(message, state)

async def checkout(message, state):
    answer = ''
    total_price = 0
    async with state.proxy() as data:
        for title, price, count_in_cart in data['products'].values():
            tp = count_in_cart * price
            answer += f'<b>{title}</b> * {count_in_cart}шт. = {tp}₽'
            total_price += tp
    await bot.send_message(message.chat.id, f'{answer}Общая сумма заказа: {total_price}₽.', reply_markup=check_markup())

@dp.message_handler(lambda message: message.text not in [all_right_message, back_message], state=CheckoutState.check_cart)
async def process_check_cart_invalid(message: Message, state: FSMContext):
    await bot.send_message(message.chat.id, 'Такого варианта не было.')

@dp.message_handler(text=back_message, state=CheckoutState.check_cart)
async def process_check_cart_back(message: Message, state: FSMContext):
    await state.finish()
    await state.set_state(UserModeState.USER)
    await process_cart(message, state)

@dp.message_handler(text=all_right_message, state=CheckoutState.check_cart)
async def process_check_cart_all_right(message: Message, state: FSMContext):
    await state.set_state(CheckoutState.next())
    await bot.send_message(message.chat.id, 'Укажите свое имя.', reply_markup=back_markup())

@dp.message_handler(text=back_message, state=CheckoutState.name)
async def process_name_back(message: Message, state: FSMContext):
    await state.set_state(CheckoutState.check_cart)
    await checkout(message, state)

@dp.message_handler(state=CheckoutState.name)
async def process_name(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
        if 'address' in data.keys():
            await confirm(message)
            await state.set_state(CheckoutState.confirm)
        else:
            await state.set_state(CheckoutState.next())
            await bot.send_message(message.chat.id, 'Укажите свой адрес места жительства.', reply_markup=back_markup())

@dp.message_handler(text=back_message, state=CheckoutState.address)
async def process_address_back(message: Message, state: FSMContext):
    async with state.proxy() as data:
        await bot.send_message(message.chat.id, f"Изменить имя с <b>{data['name']}</b>?", reply_markup=back_markup())
    await state.set_state(CheckoutState.name)

@dp.message_handler(state=CheckoutState.address)
async def process_address(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['address'] = message.text
    await confirm(message)
    await state.set_state(CheckoutState.next())

async def confirm(message):
    await bot.send_message(message.chat.id, 'Убедитесь, что все правильно оформлено и подтвердите заказ.', reply_markup=confirm_markup())

@dp.message_handler(lambda message: message.text not in [confirm_message, back_message], state=CheckoutState.confirm)
async def process_confirm_invalid(message: Message, state: FSMContext):
    await bot.send_message(message.chat.id, 'Такого варианта не было.')

@dp.message_handler(text=back_message, state=CheckoutState.confirm)
async def process_confirm_back(message: Message, state: FSMContext):
    await state.set_state(CheckoutState.address)
    async with state.proxy() as data:
        await bot.send_message(message.chat.id, f"Изменить адрес с <b>{data['address']}</b>?", reply_markup=back_markup())

@dp.message_handler(text=confirm_message, state=CheckoutState.confirm)
async def process_confirm(message: Message, state: FSMContext):
    enough_money = True
    if enough_money:
        logging.info('Deal was made.')
        async with state.proxy() as data:
            cid = message.chat.id
            products = [idx + '=' + str(quantity)
                        for idx, quantity in db.fetchall('SELECT idx, quantity FROM cart WHERE cid=?', (cid,))]
            db.query('INSERT INTO orders (cid, usr_name, usr_address, products, status) VALUES (?, ?, ?, ?, ?)',
                     (cid, data['name'], data['address'], ' '.join(products), 'новый'))
            order_id = db.get_last_row_id()
            await send_new_order_notification(bot, ADMINS, order_id, cid, data['name'], data['address'], products)
            db.query('DELETE FROM cart WHERE cid=?', (cid,))
            await bot.send_message(message.chat.id, f"""Ок! Ваш заказ уже в пути 🚀
Имя: <b>{data['name']}</b>
Адрес: <b>{data['address']}</b>""", reply_markup=ReplyKeyboardRemove())
    else:
        await bot.send_message(message.chat.id, 'У вас недостаточно денег на счете. Пополните баланс!', reply_markup=ReplyKeyboardRemove())
    await state.finish()
    await state.set_state(UserModeState.USER)
    await user_menu(message, state)
