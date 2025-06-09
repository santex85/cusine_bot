import os
from dotenv import load_dotenv

load_dotenv()

from data import config
from loader import dp, db, bot
import handlers
import filters
from aiogram import executor, types
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.dispatcher import FSMContext
import logging
from states.user_mode_state import UserModeState

filters.setup(dp)

WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.environ.get("PORT", 5000))
user_message = 'Пользователь'
admin_message = 'Админ'


@dp.message_handler(commands='start', state='*')
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    # Показываем кнопку "Админ" только если пользователь является администратором
    if message.chat.id in config.ADMINS:
        markup.row(user_message, admin_message)
    else:
        markup.row(user_message)

    await message.answer('Добро пожаловать! Выберите режим.', reply_markup=markup)
    # По умолчанию переводим пользователя в пользовательский режим
    await UserModeState.USER.set()


@dp.message_handler(text=user_message, state='*')
async def user_mode(message: types.Message, state: FSMContext):
    await UserModeState.USER.set()
    await message.answer('Включен пользовательский режим.', reply_markup=ReplyKeyboardRemove())
    # Здесь можно вызвать user_menu, если нужно сразу показать меню
    # from handlers.user.menu import user_menu
    # await user_menu(message, state)


@dp.message_handler(text=admin_message, state='*')
async def admin_mode(message: types.Message, state: FSMContext):
    cid = message.chat.id

    if cid in config.ADMINS:
        await UserModeState.ADMIN.set()
        await message.answer('Включен админский режим.', reply_markup=ReplyKeyboardRemove())
        # Здесь можно вызвать admin_menu, если нужно сразу показать меню
        # from handlers.user.menu import admin_menu
        # await admin_menu(message, state)
    else:
        # Эта логика теперь избыточна, так как кнопка не будет показана,
        # но оставим на случай, если пользователь введет "Админ" вручную
        await message.answer('У вас нет прав администратора.', reply_markup=ReplyKeyboardRemove())
        await UserModeState.USER.set()


async def on_startup(dp):
    logging.basicConfig(level=logging.INFO)
    db.create_tables()
    await bot.delete_webhook()
    if config.WEBHOOK_URL:
        await bot.set_webhook(config.WEBHOOK_URL)


async def on_shutdown():
    logging.warning("Shutting down..")
    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()
    logging.warning("Bot down")


if __name__ == '__main__':
    if "HEROKU_APP_NAME" in os.environ or "RAILWAY_PUBLIC_DOMAIN" in os.environ:
        executor.start_webhook(
            dispatcher=dp,
            webhook_path=config.WEBHOOK_PATH,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True,
            host=WEBAPP_HOST,
            port=WEBAPP_PORT,
        )
    else:
        executor.start_polling(dp, on_startup=on_startup, skip_updates=False)
