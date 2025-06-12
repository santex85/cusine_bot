from aiogram import Router, F
from aiogram.types import Message
from states.user_mode_state import UserModeState
from . import catalog, cart, delivery_status, sos # Импортируем для регистрации роутеров

router = Router()

# Определяем константы для текста кнопок
CATALOG_TEXT = '🛍️ Каталог'
CART_TEXT = '🛒 Корзина'
DELIVERY_STATUS_TEXT = '🚚 Статус доставки'
SOS_TEXT = '❓ SOS'

# Регистрируем обработчики для каждой кнопки меню
@router.message(UserModeState.USER, F.text == CATALOG_TEXT)
async def handle_catalog(message: Message, state):
    # Эта функция теперь просто вызывает основной обработчик из модуля catalog
    await catalog.process_catalog(message, state)

@router.message(UserModeState.USER, F.text == CART_TEXT)
async def handle_cart(message: Message, state):
    await cart.process_cart(message, state)

@router.message(UserModeState.USER, F.text == DELIVERY_STATUS_TEXT)
async def handle_delivery_status(message: Message, state):
    await delivery_status.process_delivery_status(message, state)
    
@router.message(UserModeState.USER, F.text == SOS_TEXT)
async def handle_sos(message: Message, state):
    await sos.process_sos(message, state)
