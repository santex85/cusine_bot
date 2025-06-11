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
# Firebase App Hosting предоставляет полный URL в переменной APP_URL
APP_URL = os.getenv("APP_URL", "https://your-app-url-is-not-set.com")

WEBHOOK_URL = f"{APP_URL.rstrip('/')}/{BOT_TOKEN}"

print("--- Configuration ---")
print(f"ADMINS: {ADMINS}")
print(f"BOT_TOKEN is set: {'Yes' if BOT_TOKEN else 'No'}")
print(f"WEBHOOK_URL: {WEBHOOK_URL}")
print("---------------------")
