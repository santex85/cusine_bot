from aiogram.fsm.state import StatesGroup, State

class CategoryState(StatesGroup):
    title = State()
    viewing = State() # Новое состояние для просмотра категории
