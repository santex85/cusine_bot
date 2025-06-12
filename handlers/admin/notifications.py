from aiogram import Router, F, types
from states.user_mode_state import UserModeState

router = Router()

@router.message(F.text == '🔔 Уведомления', UserModeState.ADMIN)
async def process_notifications(message: types.Message):
    await message.answer('Раздел "Уведомления" находится в разработке.')
