import logging
from aiogram.types import Message
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from loader import dp, db
from .menu import delivery_status as delivery_status_text
from aiogram.dispatcher import FSMContext
from states.user_mode_state import UserModeState

@dp.message_handler(text=delivery_status_text, state=UserModeState.USER)
async def process_delivery_status(message: Message, state: FSMContext):
    logging.info(f"Пользователь {message.chat.id} запросил статус заказов.")

    try:
        orders_data = db.fetchall(
            'SELECT id, cid, usr_name, usr_address, products, status FROM orders WHERE cid=?',
            (message.chat.id,)
        )
        logging.info(f"Получено {len(orders_data)} заказов для пользователя {message.chat.id}.")

    except Exception as e:
        logging.error(f"Ошибка при получении заказов для пользователя {message.chat.id} из БД: {e}")
        await message.answer("Произошла ошибка при загрузке ваших заказов.")
        return

    try:
        products_data = db.fetchall('SELECT idx, title, price FROM products')
        product_dict = {str(p[0]): {'title': p[1], 'price': p[2]} for p in products_data}
        logging.info(f"Получено {len(products_data)} товаров из БД и сформирован словарь товаров.")
    except Exception as e:
        logging.error(f"Ошибка при получении товаров из БД или формировании словаря товаров: {e}")
        product_dict = {}
        await message.answer("Предупреждение: Не удалось загрузить информацию о товарах. Детали заказа могут быть неполными.")

    if not orders_data:
        await message.answer('У вас нет активных заказов.')
    else:
        await delivery_status_answer(message, orders_data, product_dict)

async def delivery_status_answer(message: Message, orders_data: list, product_dict: dict):
    for order in orders_data:
        logging.info(f"Форматирование заказа для клиента: {order}")
        try:
            order_id, cid, usr_name, usr_address, products_string, order_status = order

            order_info = f'📦 <b>Заказ №{order_id}</b>'

            items = []
            if isinstance(products_string, str) and products_string:
                items = products_string.split(' ')
            else:
                logging.warning(f"Предупреждение: Пустая или некорректная строка товаров для заказа {order_id} пользователя {cid}.")

            total_order_price = 0
            order_items_details = ""

            if items:
                for item in items:
                    if '=' in item:
                        try:
                            item_parts = item.split('=')
                            product_id = str(item_parts[0])
                            quantity = int(item_parts[1])

                            product_info = product_dict.get(product_id, {})
                            product_name = product_info.get('title', 'Неизвестный товар')
                            product_price = product_info.get('price', 0)

                            position_total = quantity * product_price
                            order_items_details += f'  • {product_name}: {quantity} шт. по {product_price}₽ (всего: {position_total}₽)'
                            total_order_price += position_total

                        except (ValueError, IndexError) as e:
                            logging.error(f"Ошибка парсинга товара '{item}' в заказе {order_id} пользователя {cid}: {e}")
                            order_items_details += f'  • Ошибка парсинга товара: {item}'
                            continue
                    else:
                        logging.warning(f"Некорректный формат товара в строке: '{item}' для заказа {order_id} пользователя {cid}.")
                        order_items_details += f'  • Некорректный формат товара: {item}'
            else:
                order_items_details = '  (Список товаров пуст)'

            order_info += order_items_details
            order_info += f'<b>Сумма:</b> {total_order_price}₽'

            status_display = order_status if order_status is not None and order_status != "" else "Не указан"
            order_info += f'<b>Статус:</b> {status_display}'

            await message.answer(order_info, parse_mode='HTML')

        except IndexError as e:
            logging.error(f"IndexError при обработке заказа пользователя {cid}: {order}. Неверное количество столбцов? Ошибка: {e}")
            continue

        except Exception as e:
            logging.error(f"Непредвиденная ошибка при обработке заказа пользователя {cid}: {order}. Ошибка: {e}")
            continue
