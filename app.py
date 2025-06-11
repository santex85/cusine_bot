import os
from dotenv import load_dotenv
from aiohttp import web

load_dotenv()

from data import config
from loader import dp, bot, db
from aiogram import types
import logging

# --- Функции жизненного цикла ---
async def on_startup(app_instance):
    """Выполняется при старте приложения."""
    logging.basicConfig(level=logging.INFO)
    print("Приложение запускается...")
    db.create_tables()
    # Установка вебхука. URL берется из конфига.
    webhook = await bot.get_webhook_info()
    if webhook.url != config.WEBHOOK_URL:
        await bot.delete_webhook()
        await bot.set_webhook(url=config.WEBHOOK_URL)
    print(f"Вебхук установлен: {config.WEBHOOK_URL}")

async def on_shutdown(app_instance):
    """Выполняется при остановке приложения."""
    logging.warning("Приложение останавливается...")
    # Закрываем сессию бота
    await bot.session.close()
    # Удаляем вебхук при остановке
    await bot.delete_webhook()
    # Закрываем соединение с БД
    if dp.storage:
        await dp.storage.close()
        await dp.storage.wait_closed()
    logging.warning("Приложение остановлено.")

# --- Обработчик вебхука ---
async def handle_webhook(request):
    """Принимает обновления от Telegram."""
    url = str(request.url)
    index = url.rfind('/')
    token = url[index+1:]

    if token == bot.token:
        update = types.Update(**await request.json())
        await dp.process_update(update)
        return web.Response()
    else:
        return web.Response(status=403)

# --- Health Check ---
async def health_check(request):
    """Отвечает на проверки работоспособности от хостинга."""
    return web.Response(text="OK")

# --- Создание и запуск приложения ---
# Это тот самый 'app', который gunicorn будет запускать
app = web.Application()
app.router.add_post(f'/{config.BOT_TOKEN}', handle_webhook)
app.router.add_get('/health', health_check)

# Регистрируем функции on_startup и on_shutdown
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

# Эта часть нужна только для локального запуска через `python app.py`
if __name__ == '__main__':
    # Импортируем все обработчики, чтобы они зарегистрировались в dp
    import handlers
    web.run_app(app, host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))
