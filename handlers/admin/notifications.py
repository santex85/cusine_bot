from aiogram import Router, F, types, Bot
from aiogram.fsm.context import FSMContext
from loader import db
from states.user_mode_state import UserModeState
from states.notification_state import NotificationState
from keyboards.default.markups import cancel_markup, user_main_menu, admin_main_menu
import asyncio

router = Router()

CONFIRM_SEND_TEXT = "✅ Отправить"
CANCEL_SEND_TEXT = "🚫 Отмена"

def confirm_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text=CONFIRM_SEND_TEXT)],
            [types.KeyboardButton(text=CANCEL_SEND_TEXT)]
        ],
        resize_keyboard=True
    )

@router.message(F.text == '🔔 Уведомления', UserModeState.ADMIN)
async def start_notification(message: types.Message, state: FSMContext):
    await state.set_state(NotificationState.get_message)
    await message.answer(
        "Введите текст для рассылки. Вы можете прикрепить к нему одно фото.",
        reply_markup=cancel_markup()
    )

@router.message(NotificationState.get_message)
async def get_notification_message(message: types.Message, state: FSMContext):
    # Сохраняем и текст, и фото (если оно есть)
    await state.update_data(
        text=message.text or message.caption,
        photo_id=message.photo[-1].file_id if message.photo else None
    )
    
    await state.set_state(NotificationState.confirm)
    
    # Показываем превью
    await message.answer("<b>Вот как будет выглядеть ваше сообщение:</b>")
    if message.photo:
        await message.answer_photo(
            photo=message.photo[-1].file_id,
            caption=message.text or message.caption
        )
    else:
        await message.answer(message.text)
        
    await message.answer("Отправляем?", reply_markup=confirm_keyboard())


@router.message(NotificationState.confirm, F.text == CONFIRM_SEND_TEXT)
async def send_notification(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    text = data.get('text')
    photo_id = data.get('photo_id')
    
    await state.clear()
    await message.answer("Начинаю рассылку...", reply_markup=admin_main_menu())

    user_ids = db.fetchall("SELECT cid FROM users")
    successful_sends = 0
    failed_sends = 0

    for (user_id,) in user_ids:
        try:
            if photo_id:
                await bot.send_photo(chat_id=user_id, photo=photo_id, caption=text)
            else:
                await bot.send_message(chat_id=user_id, text=text)
            successful_sends += 1
            await asyncio.sleep(0.1) # Небольшая задержка, чтобы не спамить API
        except Exception as e:
            failed_sends += 1
            print(f"Failed to send message to {user_id}: {e}")

    await message.answer(
        f"✅ Рассылка завершена!"
        f"Успешно отправлено: {successful_sends}"
        f"Не удалось отправить: {failed_sends}"
    )

@router.message(NotificationState.confirm, F.text == CANCEL_SEND_TEXT)
@router.message(NotificationState.get_message, F.text == "🚫 Отмена")
async def cancel_notification(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Рассылка отменена.", reply_markup=admin_main_menu())
