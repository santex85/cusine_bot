from aiogram.dispatcher.filters.state import StatesGroup, State

class UserModeState(StatesGroup):
    """
    States for tracking user mode (User or Admin).
    """
    USER = State()
    ADMIN = State()
