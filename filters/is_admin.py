from aiogram.filters import BaseFilter
from aiogram.types import Message
from data.config import ADMINS

class IsAdmin(BaseFilter):
    """
    Фильтр для проверки, является ли пользователь администратором.
    """
    async def __call__(self, message: Message) -> bool:
        return str(message.from_user.id) in ADMINS
