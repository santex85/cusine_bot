from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from loader import db
from states.user_mode_state import UserModeState
from aiogram.filters.callback_data import CallbackData

class OrderCallbackFactory(CallbackData, prefix="order"):
    action: str # "status" или "delete"
    order_id: int

def get_orders_markup(order_id: int, current_status: str):
    buttons = [
        [types.InlineKeyboardButton(text="✅ Выполнен", callback_data=OrderCallbackFactory(action="status_completed", order_id=order_id).pack())],
        [types.InlineKeyboardButton(text="▶️ В обработке", callback_data=OrderCallbackFactory(action="status_processing", order_id=order_id).pack())],
        [types.InlineKeyboardButton(text="❌ Удалить", callback_data=OrderCallbackFactory(action="delete", order_id=order_id).pack())]
    ]
    # Удаляем кнопку для текущего статуса, чтобы избежать путаницы
    buttons = [btn for btn in buttons if current_status not in btn[0].text.lower()]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

router = Router()

@router.message(F.text == '📈 Заказы', UserModeState.ADMIN)
async def process_orders(message: types.Message):
    """
    Показывает администратору список активных заказов.
    """
    await message.answer("Загрузка заказов...")
    
    # Выбираем заказы, которые еще не выполнены
    active_orders = db.fetchall(
        "SELECT rowid, cid, usr_name, usr_address, products, status FROM orders WHERE status != 'выполнен' ORDER BY rowid DESC"
    )

    if not active_orders:
        await message.answer("Активных заказов нет.")
        return

    await message.answer("<b>Активные заказы:</b>")
    for order_id, cid, name, address, products, status in active_orders:
        products_list = products.replace('; ', '- ')
        text = (
            f"<b>Заказ №{order_id}</b>"
            f"<b>Пользователь:</b> {name} (ID: {cid})"
            f"<b>Адрес:</b> {address}"
            f"<b>Состав:</b>- {products_list}"
            f"<b>Статус:</b> {status.capitalize()}"
        )
        markup = get_orders_markup(order_id, status)
        await message.answer(text, reply_markup=markup)

@router.callback_query(OrderCallbackFactory.filter(F.action.startswith("status_")))
async def process_status_change(query: types.CallbackQuery, callback_data: OrderCallbackFactory, state: FSMContext):
    """
    Обрабатывает изменение статуса заказа.
    """
    order_id = callback_data.order_id
    new_status = "выполнен" if callback_data.action == "status_completed" else "в обработке"

    db.query("UPDATE orders SET status = ? WHERE rowid = ?", (new_status, order_id))

    await query.answer(f"Статус заказа №{order_id} изменен на '{new_status}'.")
    
    # Обновляем сообщение, чтобы убрать кнопки
    await query.message.edit_text(query.message.text + f"<b>Новый статус: {new_status.capitalize()}</b>")


@router.callback_query(OrderCallbackFactory.filter(F.action == "delete"))
async def process_delete_order(query: types.CallbackQuery, callback_data: OrderCallbackFactory, state: FSMContext):
    """
    Удаляет заказ.
    """
    order_id = callback_data.order_id
    db.query("DELETE FROM orders WHERE rowid = ?", (order_id,))
    await query.answer(f"Заказ №{order_id} удален.", show_alert=True)
    await query.message.delete()
