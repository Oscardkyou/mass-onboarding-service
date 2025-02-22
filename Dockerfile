FROM python:3.9-slim

# Установка необходимых пакетов
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя для приложения
RUN useradd -m appuser && \
    mkdir -p /app /app/uploads && \
    chown -R appuser:appuser /app

WORKDIR /app

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .
RUN chown -R appuser:appuser /app

# Переключаемся на пользователя appuser
USER appuser

# Создаем папку для загрузок и БД
RUN mkdir -p uploads

EXPOSE 5001

# Запускаем приложение через gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "4", "--timeout", "300", "app:app"]
