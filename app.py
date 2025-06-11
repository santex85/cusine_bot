import os
from dotenv import load_dotenv
from aiohttp import web

load_dotenv()

from data import config
from loader import dp, db, bot
import handlers
import filters
from aiogram import executor, types
from aiogram.dispatcher import FSMContext
import logging
from states.user_mode_state import UserModeState
from handlers.user.menu import user_menu
from handlers.admin.menu import admin_menu

filters.setup(dp)

async def on_startup(dp):
    logging.basicConfig(level=logging.INFO)
    db.create_tables()
    await bot.set_webhook(url=config.WEBHOOK_URL)

async def on_shutdown():
    logging.warning("Shutting down..")
    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()
    logging.warning("Bot down")
    
async def health_check(request):
    return web.Response(text="OK")

# Создаем приложение и добавляем health check
app = executor.get_app()
app.router.add_get('/health', health_check)

# Настраиваем on_startup и on_shutdown
executor.on_startup(on_startup)
executor.on_shutdown(on_shutdown)

# Эта часть нужна для локального запуска, на сервере она не будет выполняться
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, on_startup=on_startup, skip_updates=False)
