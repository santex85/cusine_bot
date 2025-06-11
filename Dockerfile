# Используем официальный базовый образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь остальной код проекта
COPY . .

# Указываем Gunicorn в качестве точки входа.
# Добавляем флаг -c для использования нашего конфиг. файла
CMD exec gunicorn --worker-class uvicorn.workers.UvicornWorker -c gunicorn.conf.py --bind :$PORT app:app
