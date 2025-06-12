from aiogram.fsm.state import StatesGroup, State

class ProductState(StatesGroup):
    title = State()
    body = State()
    image = State()
    price = State()
    confirm = State()

class CategoryState(StatesGroup):
    title = State()
