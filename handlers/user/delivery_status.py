from aiogram import Router, F, types
from states.user_mode_state import UserModeState

router = Router()

@router.message(F.text == '🚚 Статус доставки', UserModeState.USER)
async def process_delivery_status(message: types.Message):
    await message.answer('Этот раздел еще в разработке.')
