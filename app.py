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

# --- РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ ---
# Это самая важная строка, которой не хватало.
# Она заставляет выполниться код в handlers/__init__.py и зарегистрировать все хендлеры.
import handlers

# --- Обработчик вебхука ---
async def handle_webhook(request):
    """Принимает обновления от Telegram."""
    # Используем loader.bot и loader.dp
    url = str(request.url)
    index = url.rfind('/')
    token = url[index+1:]

    # Используем правильный атрибут _token
    if token == loader.bot._token:
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
# Используем loader.bot._token для построения пути
app.router.add_post(f'/{loader.bot._token}', handle_webhook)
app.router.add_get('/health', health_check)

# Важно! При запуске в Cloud Run не нужно вызывать web.run_app.
# Gunicorn сам запустит приложение. Этот блок остается для локальной отладки.
if __name__ == '__main__':
    print("Запуск в режиме локальной отладки...")
    web.run_app(app, host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))
