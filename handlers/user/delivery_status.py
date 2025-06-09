import logging # Добавляем логирование
from aiogram.types import Message
# Импортируем все необходимые типы, если их нет (может быть, уже есть)
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from loader import dp, db # Предполагается, что db - ваш DatabaseManager
from .menu import delivery_status as delivery_status_text # Переименовываем для ясности
# Удален import IsUser
from aiogram.dispatcher import FSMContext # Добавлен импорт FSMContext
from states.user_mode_state import UserModeState # Добавлен импорт UserModeState


# Обработчик для кнопки '🚚 Статус заказа' - срабатывает только в состоянии USER
@dp.message_handler(text=delivery_status_text, state=UserModeState.USER) # Изменен фильтр на state
async def process_delivery_status(message: Message, state: FSMContext): # Добавлен state
    logging.info(f"Пользователь {message.chat.id} запросил статус заказов.")

    try:
        # Получаем заказы пользователя. Явно указываем столбцы для контроля порядка.
        # Предполагаем схему: id, cid, usr_name, usr_address, products, status
        orders_data = db.fetchall(
            'SELECT id, cid, usr_name, usr_address, products, status FROM orders WHERE cid=?',
            (message.chat.id,)
        )
        logging.info(f"Получено {len(orders_data)} заказов для пользователя {message.chat.id}.")

    except Exception as e:
        logging.error(f"Ошибка при получении заказов для пользователя {message.chat.id} из БД: {e}")
        await message.answer("Произошла ошибка при загрузке ваших заказов.")
        return

    # Получаем данные о товарах для быстрого доступа по idx
    try:
        products_data = db.fetchall('SELECT idx, title, price FROM products')
        # Преобразуем список товаров в словарь для удобного доступа по idx
        product_dict = {str(p[0]): {'title': p[1], 'price': p[2]} for p in products_data}
        logging.info(f"Получено {len(products_data)} товаров из БД и сформирован словарь товаров.")
    except Exception as e:
        logging.error(f"Ошибка при получении товаров из БД или формировании словаря товаров: {e}")
        product_dict = {} # Инициализируем пустой словарь, чтобы избежать ошибок в дальнейшем
        await message.answer("Предупреждение: Не удалось загрузить информацию о товарах. Детали заказа могут быть неполными.")


    if not orders_data:
        await message.answer('У вас нет активных заказов.') # Возможно, "завершенных" или "в ожидании", в зависимости от того, что вы считаете "активными"
    else:
        await delivery_status_answer(message, orders_data, product_dict) # Передаем product_dict

async def delivery_status_answer(message: Message, orders_data: list, product_dict: dict):
    """
    Формирует и отправляет сообщение со статусом заказов для клиента.

    Args:
        message: Объект сообщения (для отправки ответа).
        orders_data: Список кортежей с данными заказов пользователя (SELECT id, cid, ...).
        product_dict: Словарь с информацией о товарах по idx.
    """
    response_text = "<b>Ваши заказы:</b>"
    has_orders_to_display = False # Флаг, чтобы проверить, удалось ли отобразить хоть один заказ

    for order in orders_data:
        logging.info(f"Форматирование заказа для клиента: {order}")
        try:
            # Распаковываем данные заказа из кортежа по индексам
            # Предполагаем порядок: id, cid, usr_name, usr_address, products, status
            order_id, cid, usr_name, usr_address, products_string, order_status = order

            # --- Формируем информацию об одном заказе ---
            order_info = f'📦 Заказ №<b>{order_id}</b>' # Используем ID заказа

            # --- Обработка строки с товарами ---
            items = []
            if isinstance(products_string, str) and products_string:
                items = products_string.split(' ')
            else:
                logging.warning(f"Предупреждение: Пустая или некорректная строка товаров для заказа {order_id} пользователя {cid}.")


            total_order_price = 0
            order_items_details = "" # Строка для деталей товаров в этом заказе

            if items:
                for item in items:
                    if '=' in item:
                        try:
                            item_parts = item.split('=')
                            product_id = str(item_parts[0]) # Приводим ID товара к строке для поиска
                            quantity = int(item_parts[1])

                            product_info = product_dict.get(product_id, {})
                            product_name = product_info.get('title', 'Неизвестный товар')
                            product_price = product_info.get('price', 0)

                            position_total = quantity * product_price
                            order_items_details += f'  • {product_name}: {quantity} шт. по {product_price}₽ (всего: {position_total}₽'

                            total_order_price += position_total

                        except (ValueError, IndexError) as e:
                            logging.error(f"Ошибка парсинга товара '{item}' в заказе {order_id} пользователя {cid}: {e}")
                            order_items_details += f'  • Ошибка парсинга товара: {item}'
                            continue
                    else:
                        logging.warning(f"Некорректный формат товара в строке: '{item}' для заказа {order_id} пользователя {cid}.")
                        order_items_details += f'  • Некорректный формат товара: {item}'

            else:
                 order_items_details = '  (Список товаров пуст)' # Сообщение, если товаров нет


            order_info += order_items_details # Добавляем детали товаров к информации о заказе
            order_info += f'Сумма: {total_order_price}₽' # Добавляем общую сумму заказа

            # --- Добавляем статус заказа ---
            status_display = order_status if order_status is not None and order_status != "" else "Не указан"
            order_info += f'Статус: <b>{status_display}</b>'

            # --- Добавляем информацию о заказе к общему тексту ответа ---
            response_text += order_info + "" # Разделитель между заказами
            has_orders_to_display = True # Указываем, что есть что отобразить

        except IndexError as e:
            logging.error(f"IndexError при обработке заказа пользователя {cid}: {order}. Неверное количество столбцов? Ошибка: {e}")
            # Можно добавить сообщение об ошибке в ответ пользователю, если нужно
            # response_text += f"Ошибка при загрузке деталей заказа {order_id}. Неверный формат данных."
            continue # Пропускаем некорректный заказ

        except Exception as e:
            logging.error(f"Непредвиденная ошибка при обработке заказа пользователя {cid}: {order}. Ошибка: {e}")
            # response_text += f"Непредвиденная ошибка при загрузке деталей заказа {order_id}."
            continue


    # Отправляем отформатированный текст пользователю
    if has_orders_to_display:
        await message.answer(response_text, parse_mode='HTML') # Отправляем один форматированный текст
    else:
        # Если после попыток форматирования ни один заказ не был отображен
        await message.answer("Не удалось отобразить информацию о ваших заказах.")
