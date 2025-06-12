from aiogram.filters import BaseFilter
from aiogram.types import Message

class IsUser(BaseFilter):
    """
    Фильтр для проверки, является ли пользователь обычным пользователем (не админом).
    В aiogram 3.x проще использовать инверсию фильтра IsAdmin (`~IsAdmin()`),
    но для сохранения структуры я обновлю и этот файл.
    """
    async def __call__(self, message: Message) -> bool:
        # Простая логика: если не админ, значит пользователь.
        # В реальном приложении здесь может быть более сложная проверка.
        from .is_admin import IsAdmin # Локальный импорт для избежания циклических зависимостей
        is_admin_filter = IsAdmin()
        return not await is_admin_filter(message)
