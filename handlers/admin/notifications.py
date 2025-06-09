import logging

async def send_new_order_notification(bot, admin_chat_ids: list, order_id, user_id, user_name, user_address, products_list):
    """
    Sends a notification message to the administrators about a new order.

    Args:
        bot: The bot instance.
        admin_chat_ids: A list of chat IDs of the administrators.
        order_id: The ID of the new order.
        user_id: The ID of the user who placed the order.
        user_name: The name of the user who placed the order.
        user_address: The delivery address provided by the user.
        products_list: A list of strings, where each string is "idx=quantity".
    """
    admin_message = f'🎉 Новый Заказ №<b>{order_id}</b>'
    admin_message += f'Клиент: {user_name} (<a href="tg://user?id={user_id}">{user_id}</a>)'
    admin_message += f'Адрес: {user_address}'

    admin_message += 'Товары:'

    if products_list:
        for product_info in products_list:
            item_parts = product_info.split('=')
            if len(item_parts) == 2:
                product_idx, quantity = item_parts
                # Здесь вы можете добавить получение названия и цены товара из БД, если нужно
                admin_message += f'- Товар ID: {product_idx}, Количество: {quantity}'
            else:
                admin_message += f'- Некорректный формат товара: {product_info}'

    if admin_chat_ids:
        for admin_id in admin_chat_ids:
            try:
                await bot.send_message(admin_id, admin_message, parse_mode='HTML')
            except Exception as e:
                logging.error(f"Failed to send admin notification for order {order_id} to admin {admin_id}: {e}")
    else:
        logging.warning("No admin chat IDs provided in send_new_order_notification.")
