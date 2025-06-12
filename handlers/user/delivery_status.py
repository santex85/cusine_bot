from aiogram import Router, F, types
from loader import db
from states.user_mode_state import UserModeState

router = Router()

@router.message(F.text == '🚚 Статус доставки', UserModeState.USER)
async def process_delivery_status(message: types.Message):
    """
    Показывает пользователю историю его заказов.
    """
    user_id = message.from_user.id
    # Получаем все заказы пользователя, сортируем от новых к старым
    orders = db.fetchall(
        'SELECT rowid, products, status FROM orders WHERE cid = ? ORDER BY rowid DESC',
        (user_id,)
    )

    if not orders:
        await message.answer("У вас еще нет заказов.")
        return

    await message.answer("<b>Ваши заказы:</b>")
    
    for order_id, products, status in orders:
        # Форматируем красивый вывод
        products_list = products.replace('; ', '- ')
        text = (
            f"<b>Заказ №{order_id}</b>"
            f"<b>Статус:</b> {status.capitalize()}"
            f"<b>Состав:</b>- {products_list}")
        await message.answer(text)
