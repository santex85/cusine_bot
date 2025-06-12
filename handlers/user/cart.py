from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from loader import db, bot
from states.user_mode_state import UserModeState
from keyboards.default.markups import user_main_menu
from keyboards.inline.products_from_cart import product_markup, CartProductCallbackFactory
from states.checkout_state import CheckoutState
import logging

router = Router()

@router.message(F.text == '🛒 Корзина', UserModeState.USER)
async def process_cart(message: types.Message, state: FSMContext):
    """
    Показывает содержимое корзины пользователя.
    """
    cart_products = db.fetchall(
        'SELECT pro.idx, pro.title, pro.price, cart.quantity '
        'FROM cart cart LEFT JOIN products pro ON cart.idx = pro.idx '
        'WHERE cart.cid = ?',
        (message.from_user.id,)
    )

    if not cart_products:
        await message.answer('Ваша корзина пуста.')
        return

    total_price = 0
    await message.answer('Ваша корзина:')
    
    for idx, title, price, quantity in cart_products:
        total_price += price * quantity
        markup = product_markup(idx, quantity)
        text = f"""<b>{title}</b>
Цена: {price}₽
Количество: {quantity} шт."""
        await message.answer(text, reply_markup=markup)

    await message.answer(f'Общая стоимость: {total_price}₽. Оформить заказ?',
                         reply_markup=types.ReplyKeyboardMarkup(
                             keyboard=[[types.KeyboardButton(text='📦 Оформить заказ')]],
                             resize_keyboard=True))
    await state.set_state(CheckoutState.check_cart)

@router.callback_query(CartProductCallbackFactory.filter(), UserModeState.USER)
async def product_callback_handler(query: types.CallbackQuery, callback_data: CartProductCallbackFactory, state: FSMContext):
    """
    Обрабатывает действия с товарами в корзине (увеличить, уменьшить, удалить).
    """
    user_id = query.from_user.id
    product_id = callback_data.id
    action = callback_data.action

    if action == 'increase':
        db.query('UPDATE cart SET quantity = quantity + 1 WHERE cid = ? AND idx = ?', (user_id, product_id))
    elif action == 'decrease':
        current_quantity = db.fetchone('SELECT quantity FROM cart WHERE cid = ? AND idx = ?', (user_id, product_id))[0]
        if current_quantity > 1:
            db.query('UPDATE cart SET quantity = quantity - 1 WHERE cid = ? AND idx = ?', (user_id, product_id))
        else:
            db.query('DELETE FROM cart WHERE cid = ? AND idx = ?', (user_id, product_id))
    elif action == 'delete':
        db.query('DELETE FROM cart WHERE cid = ? AND idx = ?', (user_id, product_id))

    await query.answer()
    # Обновляем сообщение с корзиной, чтобы показать изменения
    await process_cart(query.message, state)


@router.message(CheckoutState.check_cart, F.text == '📦 Оформить заказ')
async def checkout_process(message: types.Message, state: FSMContext):
    """
    Начинает процесс оформления заказа.
    """
    await state.set_state(CheckoutState.name)
    await message.answer('Введите ваше имя:', reply_markup=types.ReplyKeyboardRemove())

# ... (остальные шаги оформления заказа будут здесь) ...
# Я пока оставлю только начало, чтобы не усложнять.
# Нужно будет добавить обработчики для CheckoutState.name, CheckoutState.address и т.д.
