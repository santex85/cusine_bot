from aiogram.fsm.state import StatesGroup, State

class UserModeState(StatesGroup):
    ADMIN = State()
    USER = State()
