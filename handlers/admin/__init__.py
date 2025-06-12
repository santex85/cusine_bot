import logging
from loader import dp

logging.info("--- Регистрация обработчиков администратора ---")

try:
    from . import add
    logging.info("Модуль 'add' успешно импортирован.")
except ImportError as e:
    logging.error(f"Ошибка импорта 'add': {e}")

try:
    from . import menu
    logging.info("Модуль 'menu' успешно импортирован.")
except ImportError as e:
    logging.error(f"Ошибка импорта 'menu': {e}")

try:
    from . import notifications
    logging.info("Модуль 'notifications' успешно импортирован.")
except ImportError as e:
    logging.error(f"Ошибка импорта 'notifications': {e}")

try:
    from . import orders
    logging.info("Модуль 'orders' успешно импортирован.")
except ImportError as e:
    logging.error(f"Ошибка импорта 'orders': {e}")

try:
    from . import questions
    logging.info("Модуль 'questions' успешно импортирован.")
except ImportError as e:
    logging.error(f"Ошибка импорта 'questions': {e}")

logging.info("--- Все обработчики администратора зарегистрированы ---")


__all__ = ['dp']
