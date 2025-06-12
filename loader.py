import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio.client import Redis
from utils.db.storage import DatabaseManager
from data import config

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)

# --- Настройка хранилища Redis ---
redis_host = os.getenv('REDIS_HOST', '10.226.165.181')
redis_port = int(os.getenv('REDIS_PORT', 6379))

print(f"Connecting to Redis at {redis_host}:{redis_port}")
storage = RedisStorage(redis=Redis(host=redis_host, port=redis_port, db=0))

# --- Инициализация остальных объектов ---
db = DatabaseManager('data/database.db')

# Создаем таблицы при старте
try:
    db.create_tables()
    logging.info("Таблицы успешно созданы (если их не было).")
except Exception as e:
    logging.error(f"Ошибка при создании таблиц: {e}")

# Инициализируем бота и диспетчер с правильным синтаксисом для parse_mode
bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher(storage=storage)
