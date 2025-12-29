#!/usr/bin/env bash
# build.sh

set -o errexit

# Устанавливаем зависимости
pip install -r requirements.txt

# Применяем миграции базы данных
python manage.py migrate --noinput

python manage.py create_superuser_if_none_exists \
  --username=admin \
  --email=admin@example.com \
  --password=123123

# Собираем статические файлы
python manage.py collectstatic --noinput
