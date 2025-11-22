FROM python:3.10-slim

# Установка зависимостей системы
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копирование зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Создание необходимых директорий
RUN mkdir -p /app/data

# Переменные окружения
ENV PYTHONUNBUFFERED=1

# Запуск бота
CMD ["python", "bot.py"]
