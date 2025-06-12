# backend/Dockerfile

# 1. Базовый образ
FROM python:3.11-slim

# 2. Переменные для Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Устанавливаем рабочую директорию
WORKDIR /app

# Установка netcat для ожидания БД
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

# 4. Копируем файл зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Копируем весь код приложения в контейнер
COPY . .

# 6. Делаем скрипт entrypoint.sh исполняемым
RUN chmod +x /app/entrypoint.sh

# 7. По умолчанию запускаем entrypoint, затем команду запуска
ENTRYPOINT ["/app/entrypoint.sh"]
# Для dev: запустим runserver. Можно менять команду в Compose.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]