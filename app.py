import os
from dotenv import load_dotenv
from aiohttp import web

load_dotenv()

from data import config
# Импортируем сам модуль loader
import loader
from aiogram import types
import logging

# Инициализация логирования
logging.basicConfig(level=logging.INFO)

# --- ИНИЦИАЛИЗАЦИЯ ПЕРЕД ЗАПУСКОМ ---
# Вызываем нашу функцию инициализации один раз
loader.on_startup_init() 

# --- Обработчик вебхука ---
async def handle_webhook(request):
    """Принимает обновления от Telegram."""
    # Используем loader.bot и loader.dp
    url = str(request.url)
    index = url.rfind('/')
    token = url[index+1:]

    if token == loader.bot.token:
        update = types.Update(**await request.json())
        await loader.dp.process_update(update)
        return web.Response()
    else:
        return web.Response(status=403)

# --- Health Check ---
async def health_check(request):
    """Отвечает на проверки работоспособности от хостинга."""
    return web.Response(text="OK")

# --- Создание и запуск приложения ---
app = web.Application()
# Используем loader.bot.token для построения пути
app.router.add_post(f'/{config.BOT_TOKEN}', handle_webhook)
app.router.add_get('/health', health_check)

# Важно! При запуске в Cloud Run не нужно вызывать web.run_app.
# Gunicorn сам запустит приложение. Этот блок остается для локальной отладки.
if __name__ == '__main__':
    # Импортируем все обработчики, чтобы они зарегистрировались в dp
    import handlers
    print("Запуск в режиме локальной отладки...")
    # Используем loader.db
    loader.db.create_tables()
    web.run_app(app, host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))
