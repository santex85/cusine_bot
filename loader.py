import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage  # Импортируем MemoryStorage
from utils.db.storage import DatabaseManager
from data import config

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)

# --- Настройка хранилища FSM ---
# Заменяем RedisStorage на MemoryStorage, чтобы избежать проблем с подключением
storage = MemoryStorage()
logging.warning("Using MemoryStorage for FSM. States will be lost on restart.")

# --- Инициализация остальных объектов ---
db = DatabaseManager('data/database.db')

# Создаем таблицы при старте
try:
    db.create_tables()
    logging.info("Таблицы успешно созданы (если их не было).")
except Exception as e:
    logging.error(f"Ошибка при создании таблиц: {e}")

# Инициализируем бота и диспетчер
bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher(storage=storage)
