import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Получаем строку с ID админов, убираем пробелы и разделяем по запятой
admins_str = os.getenv("ADMINS", "")
ADMINS = [admin.strip() for admin in admins_str.split(',') if admin]
