from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from loader import db
from states.user_mode_state import UserModeState
from keyboards.default.markups import user_main_menu
from keyboards.inline.products_from_cart import product_markup, CartProductCallbackFactory
from states.checkout_state import CheckoutState
import logging
import json

router = Router()


async def show_cart(message: types.Message, state: FSMContext):
    """
    Показывает содержимое корзины и итоговую стоимость.
    """
    cart_products = db.fetchall(
        'SELECT pro.idx, pro.title, pro.price, cart.quantity '
        'FROM cart cart LEFT JOIN products pro ON cart.idx = pro.idx '
        'WHERE cart.cid = ?',
        (message.from_user.id,)
    )

    if not cart_products:
        await message.answer('Ваша корзина пуста.', reply_markup=user_main_menu())
        return

    total_price = 0
    await message.answer('Ваша корзина:')
    
    for idx, title, price, quantity in cart_products:
        # Проверка на случай, если товар удалили из каталога, а он остался в корзине
        if title is None or price is None:
            db.query('DELETE FROM cart WHERE cid = ? AND idx = ?', (message.from_user.id, idx))
            logging.info(f"Removed unavailable product {idx} from cart for user {message.from_user.id}")
            continue

        total_price += price * quantity
        markup = product_markup(idx, quantity)
        text = f"""<b>{title}</b>
Цена: {price}₽
Количество: {quantity} шт."""
        await message.answer(text, reply_markup=markup)

    await message.answer(f'Общая стоимость: {total_price}₽.',
                         reply_markup=types.ReplyKeyboardMarkup(
                             keyboard=[
                                 [types.KeyboardButton(text='📦 Оформить заказ')],
                                 [types.KeyboardButton(text='◀️ Назад в меню')]
                             ],
                             resize_keyboard=True))
    await state.set_state(CheckoutState.check_cart)


@router.message(F.text == '🛒 Корзина', UserModeState.USER)
async def process_cart_command(message: types.Message, state: FSMContext):
    await show_cart(message, state)


@router.message(F.text == '◀️ Назад в меню', CheckoutState.check_cart)
async def back_to_main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Вы вернулись в главное меню.", reply_markup=user_main_menu())


@router.callback_query(CartProductCallbackFactory.filter(), UserModeState.USER)
async def product_callback_handler(query: types.CallbackQuery, callback_data: CartProductCallbackFactory, state: FSMContext):
    user_id = query.from_user.id
    product_id = callback_data.id

    if callback_data.action == 'increase':
        db.query('UPDATE cart SET quantity = quantity + 1 WHERE cid = ? AND idx = ?', (user_id, product_id))
    elif callback_data.action == 'decrease':
        # Безопасное уменьшение: сначала вычитаем, потом удаляем если 0 или меньше
        db.query('UPDATE cart SET quantity = quantity - 1 WHERE cid = ? AND idx = ?', (user_id, product_id))
        db.query('DELETE FROM cart WHERE cid = ? AND idx = ? AND quantity <= 0', (user_id, product_id))
    elif callback_data.action == 'delete':
        db.query('DELETE FROM cart WHERE cid = ? AND idx = ?', (user_id, product_id))

    await query.answer()
    # Обновляем вид корзины, удаляя старое сообщение и отправляя новое
    await query.message.delete()
    await show_cart(query.message, state)


# --- Оформление заказа (Checkout FSM) ---

@router.message(CheckoutState.check_cart, F.text == '📦 Оформить заказ')
async def checkout_start(message: types.Message, state: FSMContext):
    await state.set_state(CheckoutState.name)
    await message.answer('Введите ваше имя:', reply_markup=types.ReplyKeyboardRemove())


@router.message(CheckoutState.name)
async def checkout_process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(CheckoutState.address)
    await message.answer('Спасибо! Теперь введите ваш адрес доставки:')


@router.message(CheckoutState.address)
async def checkout_process_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    
    # Получаем все данные для подтверждения
    data = await state.get_data()
    user_name = data.get('name')
    user_address = data.get('address')
    
    cart_products = db.fetchall(
        'SELECT pro.title, pro.price, cart.quantity '
        'FROM cart cart LEFT JOIN products pro ON cart.idx = pro.idx '
        'WHERE cart.cid = ?',
        (message.from_user.id,)
    )

    if not cart_products:
        await message.answer('Ваша корзина пуста. Оформление заказа отменено.', reply_markup=user_main_menu())
        await state.clear()
        return

    total_price = 0
    products_list = []
    for title, price, quantity in cart_products:
        total_price += price * quantity
        products_list.append(f"{title} x{quantity}")

    # Сохраняем итоговые данные в состояние
    await state.update_data(products="; ".join(products_list), total_price=total_price)

    # Показываем финальное подтверждение
    await message.answer(
        f"<b>Пожалуйста, проверьте данные:</b>"
        f"<b>Имя:</b> {user_name}"
        f"<b>Адрес:</b> {user_address}"
        f"<b>Товары:</b>" + "".join([f"- {item}" for item in products_list]) + ""
        f"<b>Итого к оплате:</b> {total_price}"
        f"Все верно?",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text='✅ Все верно')]],
            resize_keyboard=True
        )
    )
    await state.set_state(CheckoutState.confirm)


@router.message(CheckoutState.confirm, F.text == '✅ Все верно')
async def checkout_finish(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()

    # Сохраняем заказ в базу данных
    db.query(
        'INSERT INTO orders (cid, usr_name, usr_address, products, status) VALUES (?, ?, ?, ?, ?)',
        (user_id, data.get('name'), data.get('address'), data.get('products'), 'в обработке')
    )

    # Очищаем корзину пользователя
    db.query('DELETE FROM cart WHERE cid = ?', (user_id,))

    await message.answer(
        '<b>Спасибо за ваш заказ!</b>'
        'Мы свяжемся с вами в ближайшее время для уточнения деталей.'
        'Статус заказа можно будет проверить в разделе "🚚 Статус доставки".',
        reply_markup=user_main_menu()
    )
    await state.clear()
