import os
import logging
from dotenv import load_dotenv
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from loader import dp, bot, db

# --- ИМПОРТ ОБРАБОТЧИКОВ ---
# Импортируем все роутеры из наших модулей
from handlers.admin import menu as admin_menu, add as admin_add, orders, notifications, questions
from handlers.user import catalog, cart, delivery_status, sos
from handlers import start

async def on_startup(bot_instance: Bot):
    """
    Выполняется при старте приложения. Устанавливает вебхук.
    """
    webhook_url = f"{os.getenv('APP_URL')}/{bot_instance.token}"
    await bot_instance.set_webhook(
        url=webhook_url,
        allowed_updates=dp.resolve_used_update_types(),
        drop_pending_updates=True
    )
    logging.info(f"Webhook has been set to: {webhook_url}")

async def on_shutdown(bot_instance: Bot):
    """
    Выполняется при остановке приложения. Удаляет вебхук.
    """
    logging.warning('Shutting down..')
    await bot_instance.delete_webhook()
    if db.conn:
        db.conn.close()
    logging.warning('Bot down')

async def handle_webhook(request):
    """
    Принимает и обрабатывает обновления от Telegram.
    """
    url = str(request.url)
    token = url.split('/')[-1]

    if token == bot.token:
        try:
            update = types.Update(**await request.json())
            await dp.feed_update(bot=bot, update=update)
            return web.Response()
        except Exception as e:
            logging.error(f"Error processing update: {e}", exc_info=True)
            return web.Response(status=500)
    else:
        return web.Response(status=403)

async def health_check(request):
    """Отвечает на проверки работоспособности."""
    return web.Response(text="OK")

def main():
    """Основная функция для настройки и запуска приложения."""
    load_dotenv()

    # --- РЕГИСТРАЦИЯ РОУТЕРОВ ---
    dp.include_router(start.router)
    # Админские роутеры
    dp.include_router(admin_menu.router)
    dp.include_router(admin_add.router)
    dp.include_router(orders.router)
    dp.include_router(notifications.router)
    dp.include_router(questions.router)
    # Пользовательские роутеры
    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(delivery_status.router)
    dp.include_router(sos.router)

    # Регистрируем функции жизненного цикла
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Создаем веб-приложение
    app = web.Application()
    app.router.add_post(f'/{bot.token}', handle_webhook)
    app.router.add_get('/health', health_check)

    return app

# Создаем приложение для Gunicorn
app = main()

if __name__ == '__main__':
    web.run_app(app, host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))
