# Этап 1: Используем официальный образ Python как базовый
FROM python:3.11-slim

# Устанавливаем переменные окружения для Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем только файл с зависимостями, чтобы использовать кэш Docker
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь остальной код приложения в рабочую директорию
COPY . .

# Сообщаем Docker, что контейнер будет слушать порт, который предоставит хостинг
EXPOSE 8080

# Команда для запуска приложения при старте контейнера
# Gunicorn будет слушать на всех интерфейсах на порту, который ему предоставит хостинг
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "app:app"]
