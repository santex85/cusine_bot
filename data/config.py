import os

from dotenv import load_dotenv

load_dotenv()

ADMINS_STR = os.getenv("ADMINS", "")
print(f"ADMINS_STR from env: {ADMINS_STR}")
try:
    ADMINS = list(map(int, ADMINS_STR.split(",")))
    print(f"ADMINS list: {ADMINS}")
except ValueError as e:
    print(f"Error converting ADMINS to int: {e}. ADMINS_STR was: {ADMINS_STR}")


BOT_TOKEN = os.getenv("BOT_TOKEN")

PROJECT_NAME = os.getenv("PROJECT_NAME")

# Heroku webhook
# WEBHOOK_HOST = f"https://{PROJECT_NAME}.herokuapp.com"
# WEBHOOK_PATH = '/webhook/' + BOT_TOKEN

# Railway webhook
WEBHOOK_HOST = os.getenv("RAILWAY_PUBLIC_DOMAIN")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH")

if WEBHOOK_HOST and WEBHOOK_PATH:
    WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
else:
    WEBHOOK_URL = None

ADMINS = list(map(int, os.getenv("ADMINS", "").split(",")))
