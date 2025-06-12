from aiogram import Router, F, types
from states.user_mode_state import UserModeState

router = Router()

@router.message(F.text == '❓ SOS', UserModeState.USER)
async def process_sos(message: types.Message):
    await message.answer('Этот раздел еще в разработке.')
