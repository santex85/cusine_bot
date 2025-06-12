import logging
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from loader import dp, db, bot
from handlers.admin.menu import orders as orders_text
from aiogram.dispatcher import FSMContext
from states.user_mode_state import UserModeState

@dp.message_handler(text=orders_text, state=UserModeState.ADMIN)
async def process_orders(message: Message, state: FSMContext):
    logging.info("Администратор запросил список заказов.")
    try:
        orders_data = db.fetchall('SELECT id, cid, usr_name, usr_address, products, status FROM orders')
        logging.info(f"Получено {len(orders_data)} заказов из БД.")
    except Exception as e:
        logging.error(f"Ошибка при получении заказов из БД: {e}")
        await bot.send_message(message.chat.id, "Произошла ошибка при загрузке заказов.")
        return
    try:
        products_data = db.fetchall('SELECT idx, title, price FROM products')
        product_dict = {str(p[0]): {'title': p[1], 'price': p[2]} for p in products_data}
        logging.info(f"Получено {len(products_data)} товаров из БД и сформирован словарь.")
    except Exception as e:
        logging.error(f"Ошибка при получении товаров из БД или формировании словаря: {e}")
        product_dict = {}
        await bot.send_message(message.chat.id, "Предупреждение: Не удалось загрузить информацию о товарах. Цены и названия могут быть некорректны.")
    if not orders_data:
        await bot.send_message(message.chat.id, 'У вас нет заказов.')
    else:
        await order_answer(message, orders_data, product_dict)

async def order_answer(message: Message, orders_data: list, product_dict: dict):
    for order in orders_data:
        logging.info(f"Обрабатывается заказ из БД: {order}")
        try:
            order_id, cid, usr_name, usr_address, products_string, order_status = order
            res = f'Заказ №<b>{order_id}</b>'
            res += f'Клиент: {usr_name if usr_name is not None else "Не указан"} (<a href="tg://user?id={cid}">{cid if cid is not None else "Не указан"}</a>)'
            res += f'Адрес: {usr_address if usr_address is not None else "Не указан"}'
            total_order_price = 0
            items = []
            if isinstance(products_string, str) and products_string:
                items = products_string.split(' ')
            else:
                logging.warning(f"Предупреждение: Некорректная или пустая строка товаров для заказа {order_id}. products_string: '{products_string}'")
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
                            res += f'{product_name}: {quantity} шт. по {product_price} руб. (всего: {position_total} руб.)'
                            total_order_price += position_total
                        except (ValueError, IndexError) as e:
                            logging.error(f"Ошибка парсинга товара '{item}' в заказе {order_id}: {e}")
                            res += f'  • Ошибка парсинга товара: {item}'
                            continue
                    else:
                        logging.warning(f"Некорректный формат товара в строке: '{item}' для заказа {order_id}")
                        res += f'  • Некорректный формат товара: {item}'
            else:
                res += '  (Список товаров пуст или не удалось распарсить)'
            res += f'Общая стоимость заказа: {total_order_price} руб.'
            status_display = order_status if order_status is not None and order_status != "" else "Не указан"
            res += f'Статус: <b>{status_display}</b>'
            keyboard = InlineKeyboardMarkup()
            callback_data_done = f'status_done_{order_id}'
            done_button = InlineKeyboardButton(text='Отметить как выполненный', callback_data=callback_data_done)
            keyboard.add(done_button)
            delete_callback_data = f'delete_order_{order_id}'
            delete_button = InlineKeyboardButton(text='Удалить заказ', callback_data=delete_callback_data)
            keyboard.add(delete_button)
            await bot.send_message(message.chat.id, res, reply_markup=keyboard, parse_mode='HTML')
        except IndexError as e:
            logging.error(f"IndexError при обработке заказа: {order}. Вероятно, неверное количество столбцов в кортеже. Ошибка: {e}")
            await bot.send_message(message.chat.id, f"Ошибка при обработке заказа: {order}. Неверный формат данных.")
            continue
        except Exception as e:
            logging.error(f"Непредвиденная ошибка при обработке заказа: {order}. Ошибка: {e}")
            await bot.send_message(message.chat.id, f"Непредвиденная ошибка при обработке заказа: {order}.")
            continue

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('status_done_'), state=UserModeState.ADMIN)
async def process_status_done(callback_query: CallbackQuery, state: FSMContext):
    logging.info(f"Администратор отметил заказ как выполненный: {callback_query.data}")
    try:
        order_id_str = callback_query.data.split('_')[-1]
        order_id = int(order_id_str)
    except (ValueError, IndexError):
        logging.error(f"Некорректный формат callback_data для изменения статуса: {callback_query.data}")
        await callback_query.answer("Ошибка: Неверный формат данных заказа.", show_alert=True)
        return
    try:
        db.query('UPDATE orders SET status = ? WHERE id = ?', ('выполнен', order_id))
        logging.info(f"Статус заказа {order_id} успешно изменен на 'выполнен'.")
        await callback_query.answer("Статус заказа изменен на 'выполнен'", show_alert=False)
    except Exception as e:
        logging.error(f"Ошибка при обновлении статуса заказа {order_id} в БД: {e}")
        await callback_query.answer("Произошла ошибка при изменении статуса.", show_alert=True)

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('delete_order_'), state=UserModeState.ADMIN)
async def process_delete_order(callback_query: CallbackQuery, state: FSMContext):
    logging.info(f"Администратор запросил удаление заказа: {callback_query.data}")
    try:
        order_id_str = callback_query.data.split('_')[-1]
        order_id = int(order_id_str)
    except (ValueError, IndexError):
        logging.error(f"Некорректный формат callback_data для удаления: {callback_query.data}")
        await callback_query.answer("Ошибка: Неверный формат данных заказа.", show_alert=True)
        return
    try:
        db.query('DELETE FROM orders WHERE id = ?', (order_id,))
        logging.info(f"Заказ {order_id} успешно удален из БД.")
        await callback_query.answer(f"Заказ {order_id} удален", show_alert=False)
        await callback_query.message.delete()
        logging.info(f"Сообщение для заказа {order_id} удалено из чата.")
    except Exception as e:
        logging.error(f"Ошибка при удалении заказа {order_id} из БД: {e}")
        await callback_query.answer("Произошла ошибка при удалении заказа.", show_alert=True)
