# Указываем базовый образ
FROM python:3.12.3-alpine

# Устанавливаем обновления и необходимые системные зависимости
RUN apt-get update && apt-get install -y \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файлы проекта в контейнер
COPY . /app

# Копируем файл зависимостей и устанавливаем Python зависимости
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копируем файл конфигурации окружения
COPY .env .env

# Запуск Redis в качестве фонового процесса
RUN redis-server --daemonize yes

# Открываем порт для взаимодействия с ботом
EXPOSE 8000

# Команда запуска бота
CMD ["python", "main.py"]
