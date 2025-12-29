#!/usr/bin/env bash
# build.sh

set -o errexit

# Устанавливаем зависимости
pip install -r requirements.txt

# Применяем миграции базы данных
python manage.py migrate --noinput

# Собираем статические файлы
python manage.py collectstatic --noinput