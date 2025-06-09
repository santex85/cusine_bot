# Используем более современный и безопасный образ Python
FROM python:3.11.10-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Обновляем pip и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем остальную часть приложения
COPY . .

# Создаем пользователя без прав root для безопасности
RUN useradd --create-home appuser
USER appuser

# Запускаем приложение
CMD ["python", "app.py"]
