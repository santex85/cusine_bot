import asyncio
import os
from dotenv import load_dotenv

print("--- Запуск скрипта установки вебхука ---")

# Загружаем переменные окружения
load_dotenv()

# Импортируем сам модуль loader
import loader
from data.config import WEBHOOK_URL

async def main():
    """
    Основная функция для установки вебхука.
    """
    # Сначала инициализируем объекты через модуль
    loader.on_startup_init()
    
    # Теперь, когда объекты инициализированы, мы можем быть уверены,
    # что loader.bot и loader.dp существуют.
    
    # Проверяем наличие токена напрямую через loader, используя правильный атрибут _token
    if not loader.bot._token:
        print("ОШИБКА: BOT_TOKEN не был загружен при инициализации.")
        return

    if not WEBHOOK_URL or 'not-set' in WEBHOOK_URL:
        print(f"ОШИБКА: Переменная окружения APP_URL не установлена. WEBHOOK_URL: {WEBHOOK_URL}")
        return

    print(f"Текущий URL вебхука: {WEBHOOK_URL}")

    # Получаем информацию о текущем вебхуке, используя loader.bot
    try:
        webhook_info = await loader.bot.get_webhook_info()
        print(f"Текущий вебхук в Telegram: {webhook_info.url}")

        if webhook_info.url == WEBHOOK_URL:
            print("Вебхук уже установлен на правильный URL. Ничего не делаем.")
        else:
            print("URL вебхука отличается. Устанавливаем новый...")
            await loader.bot.set_webhook(url=WEBHOOK_URL)
            print("Новый вебхук успешно установлен.")

    except Exception as e:
        print(f"Произошла ошибка при установке вебхука: {e}")
    finally:
        # Важно закрыть сессию бота, чтобы скрипт корректно завершился
        # Проверяем, что bot не None перед закрытием сессии
        if loader.bot and loader.bot.session:
            await loader.bot.session.close()
            print("Сессия бота закрыта.")

if __name__ == "__main__":
    # Запускаем асинхронную функцию
    asyncio.run(main())

print("--- Скрипт установки вебхука завершил работу ---")
