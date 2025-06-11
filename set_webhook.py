import asyncio
import os
from dotenv import load_dotenv

print("--- Запуск скрипта установки вебхука ---")

# Загружаем переменные окружения
load_dotenv()

# Импортируем нужные компоненты
# Убедитесь, что пути импорта корректны для вашего проекта
from loader import bot
from data.config import WEBHOOK_URL, BOT_TOKEN

async def main():
    """
    Основная функция для установки вебхука.
    """
    if not BOT_TOKEN:
        print("ОШИБКА: Секрет BOT_TOKEN не найден.")
        return

    if not WEBHOOK_URL or 'not-set' in WEBHOOK_URL:
        print(f"ОШИБКА: Переменная окружения APP_URL не установлена. WEBHOOK_URL: {WEBHOOK_URL}")
        return

    print(f"Текущий URL вебхука: {WEBHOOK_URL}")

    # Получаем информацию о текущем вебхуке
    try:
        webhook_info = await bot.get_webhook_info()
        print(f"Текущий вебхук в Telegram: {webhook_info.url}")

        if webhook_info.url == WEBHOOK_URL:
            print("Вебхук уже установлен на правильный URL. Ничего не делаем.")
        else:
            print("URL вебхука отличается. Устанавливаем новый...")
            await bot.set_webhook(url=WEBHOOK_URL)
            print("Новый вебхук успешно установлен.")

    except Exception as e:
        print(f"Произошла ошибка при установке вебхука: {e}")
    finally:
        # Важно закрыть сессию бота, чтобы скрипт корректно завершился
        await bot.session.close()
        print("Сессия бота закрыта.")

if __name__ == "__main__":
    # Запускаем асинхронную функцию
    asyncio.run(main())

print("--- Скрипт установки вебхука завершил работу ---")
