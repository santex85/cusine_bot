FROM python:3.11-slim
WORKDIR /app

# 1. Копируем ТОЛЬКО файл с зависимостями
COPY requirements.txt .

# 2. Устанавливаем зависимости. Этот слой будет кэшироваться.
RUN pip install --no-cache-dir -r requirements.txt

# 3. Теперь копируем весь остальной код приложения
COPY . .

# 4. Команда запуска остается прежней
CMD exec gunicorn --worker-class aiohttp.worker.GunicornWebWorker --bind :$PORT app:app
