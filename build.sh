#!/usr/bin/env bash
# build.sh

set -o errexit

echo "=== 1. Установка зависимостей ==="
pip install -r requirements.txt

echo "=== 2. Показываю список миграций ==="
python manage.py showmigrations

echo "=== 3. Применяем миграции базы данных ==="
python manage.py migrate --noinput

echo "=== 4. Создаём суперпользователя (если нет) ==="
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'ваш_надёжный_пароль')
    print('Суперпользователь создан')
else:
    print('Суперпользователь уже существует')
EOF

echo "=== 5. Создаём тестовые категории (если нет) ==="
python manage.py shell << EOF
from store.models import Category

if Category.objects.count() == 0:
    Category.objects.create(name='Инструменты', slug='tools')
    Category.objects.create(name='Материалы', slug='materials')
    print('Тестовые категории созданы')
else:
    print('Категории уже существуют')
EOF

echo "=== 6. Собираем статические файлы ==="
python manage.py collectstatic --noinput

echo "=== Сборка успешно завершена ==="
