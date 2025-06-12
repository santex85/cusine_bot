from aiogram import Router, F, types
from states.user_mode_state import UserModeState

router = Router()

@router.message(F.text == '❓ Вопросы', UserModeState.ADMIN)
async def process_questions(message: types.Message):
    await message.answer('Раздел "Вопросы" находится в разработке.')
