from aiogram.fsm.state import StatesGroup, State

class NotificationState(StatesGroup):
    get_message = State()
    confirm = State()
