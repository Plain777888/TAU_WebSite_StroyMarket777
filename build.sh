#!/usr/bin/env bash
# build.sh - SAFE VERSION

set -o errexit

echo "=== 1. Установка зависимостей ==="
pip install -r requirements.txt

echo "=== 2. Показываю ВСЕ миграции (должен быть store) ==="
python manage.py showmigrations

echo "=== 3. Применяем миграции ==="
python manage.py migrate --noinput

echo "=== 4. ТОЛЬКО ПРОВЕРКА: создаём суперпользователя БЕЗ профиля ==="
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()

if not User.objects.filter(username='admin').exists():
    # Временно отключаем сигнал создания профиля
    from django.db.models import signals
    from store import models
    signals.post_save.disconnect(models.create_user_profile, sender=User)

    # Создаём пользователя
    user = User.objects.create_superuser('admin', 'admin@example.com', 'Admin123!smartexamplewordnumbertwoandrdfmodsfklsmasmdla')
    print(f'Суперпользователь {user.username} создан (профиль будет создан позже)')
else:
    print('Суперпользователь уже существует')
EOF

echo "=== 5. Сбор статических файлов ==="
python manage.py collectstatic --noinput

echo "=== СБОРКА ЗАВЕРШЕНА ==="