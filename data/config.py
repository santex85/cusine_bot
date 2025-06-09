import os
from dotenv import load_dotenv

load_dotenv()

# --- Настройка администраторов ---
ADMINS_STR = os.getenv("ADMINS", "")
ADMINS = []
if ADMINS_STR:
    try:
        ADMINS = [int(admin_id) for admin_id in ADMINS_STR.split(",")]
    except ValueError as e:
        print(f"Ошибка при обработке ADMINS: {e}. Проверьте формат переменной окружения.")

# --- Токен бота ---
BOT_TOKEN = os.getenv("BOT_TOKEN")

# --- Настройка вебхука ---
WEBHOOK_URL = None
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"

# Проверяем, запущено ли приложение в среде Google Cloud (Firebase)
if os.environ.get("K_SERVICE"):
    # Формируем URL на основе стандартных переменных Google Cloud
    # https://<service-name>-<project-hash>-<region>.a.run.app
    # Google Cloud предоставляет SERVICE_URL, но для надежности соберем его сами, если его нет
    service_url = os.environ.get("SERVICE_URL") # Переменная, которую может предоставлять App Hosting
    if service_url:
        WEBHOOK_URL = f"{service_url}{WEBHOOK_PATH}"
    else:
        # Если SERVICE_URL не предоставлен, пытаемся собрать его вручную
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        region = os.environ.get("REGION", "us-central1") # us-central1 - регион по умолчанию
        service_name = os.environ.get("K_SERVICE")
        if project_id and service_name:
             # Это более сложный, но надежный способ, если стандартные URL не работают
             # Однако, для Firebase App Hosting обычно достаточно простого относительного пути
             # Для простоты и надежности будем полагаться на относительный путь,
             # так как Firebase App Hosting сам знает свой домен.
             # Поэтому мы просто устанавливаем WEBHOOK_PATH, а URL оставляем пустым,
             # чтобы aiogram использовал относительный путь.
             WEBHOOK_URL = "" # Пустой URL заставит aiogram использовать относительный путь
        
# Для локальной разработки, если нужно (например, через ngrok)
# else:
#     WEBHOOK_URL = "https://your-ngrok-url.ngrok.io"

print("--- Configuration ---")
print(f"ADMINS: {ADMINS}")
print(f"BOT_TOKEN is set: {'Yes' if BOT_TOKEN else 'No'}")
print(f"WEBHOOK_PATH: {WEBHOOK_PATH}")
print(f"WEBHOOK_URL: {WEBHOOK_URL}")
print("---------------------")
