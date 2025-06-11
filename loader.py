from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from utils.db.storage import DatabaseManager
from data import config

# Объявляем переменные, но не инициализируем их
bot: Bot | None = None
storage: MemoryStorage | None = None
dp: Dispatcher | None = None
db: DatabaseManager | None = None

def on_startup_init():
    """
    Инициализирует все ключевые объекты.
    Эта функция должна быть вызвана один раз при старте.
    """
    global bot, storage, dp, db
    
    print("Инициализация объектов: Bot, Dispatcher, DB...")
    
    bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)
    db = DatabaseManager('data/database.db')
    
    print("Инициализация завершена.")
