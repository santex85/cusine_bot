from aiogram.fsm.state import StatesGroup, State

class SosState(StatesGroup):
    question = State()
