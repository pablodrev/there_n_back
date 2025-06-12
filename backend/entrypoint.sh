#!/usr/bin/env sh
set -e

# Ожидаем появления PostgreSQL.
# Переменные окружения:
#   DB_HOST, DB_PORT (оставляем 5432 по умолчанию)

echo "Waiting for PostgreSQL at ${DB_HOST:-db}:${DB_PORT:-5432}..."
# Если DB_HOST не задан, по умолчанию docker-compose hostname 'db'.
while ! nc -z ${DB_HOST:-db} ${DB_PORT:-5432}; do
  sleep 1
done
echo "PostgreSQL is up - continuing"

# Применяем миграции
echo "Apply database migrations"
python manage.py migrate --noinput

# Затем выполняем CMD
exec "$@"