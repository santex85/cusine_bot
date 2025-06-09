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

# Проверяем, запущено ли приложение в облачной среде (Firebase/Google Cloud)
# Переменная SERVICE_URL предоставляется хостингом
service_url = os.environ.get("SERVICE_URL")
if service_url:
    WEBHOOK_URL = f"{service_url.rstrip('/')}{WEBHOOK_PATH}"

print("--- Configuration ---")
print(f"ADMINS: {ADMINS}")
print(f"BOT_TOKEN is set: {'Yes' if BOT_TOKEN else 'No'}")
print(f"WEBHOOK_PATH: {WEBHOOK_PATH}")
print(f"WEBHOOK_URL: {WEBHOOK_URL}")
print("---------------------")
