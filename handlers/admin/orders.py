from aiogram import Router, F, types
from states.user_mode_state import UserModeState

router = Router()

@router.message(F.text == '📈 Заказы', UserModeState.ADMIN)
async def process_orders(message: types.Message):
    await message.answer('Раздел "Заказы" находится в разработке.')
