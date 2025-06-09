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

WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.environ.get("PORT", 8080))

@dp.message_handler(commands='start', state='*')
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    if message.chat.id in config.ADMINS:
        await UserModeState.ADMIN.set()
        await admin_menu(message, state)
    else:
        await UserModeState.USER.set()
        await user_menu(message, state)

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

if __name__ == '__main__':
    if os.environ.get("K_SERVICE"):
        print("Starting in webhook mode...")
        app = executor.get_app()
        app.router.add_get('/health', health_check)
        
        executor.start_webhook(
            dispatcher=dp,
            webhook_path=config.WEBHOOK_PATH,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True,
            host=WEBAPP_HOST,
            port=WEBAPP_PORT,
            app=app,
        )
    else:
        print("Starting in polling mode...")
        executor.start_polling(dp, on_startup=on_startup, skip_updates=False)
