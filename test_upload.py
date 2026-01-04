# check_models.py
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'construction_store.settings')

import django
django.setup()

print("🔍 Проверяем модели в проекте...")

# Импортируем все модели
try:
    from products.models import Product as Product1
    print("✅ Найдена модель Product в приложении 'products'")
    print(f"   Путь: {Product1.__module__}")
except ImportError as e:
    print(f"❌ Нет модели Product в 'products': {e}")

try:
    from store.models import Product as Product2
    print("✅ Найдена модель Product в приложении 'store'")
    print(f"   Путь: {Product2.__module__}")
except ImportError as e:
    print(f"❌ Нет модели Product в 'store': {e}")

# Проверяем INSTALLED_APPS
from django.conf import settings
print(f"\n📋 INSTALLED_APPS:")
for app in settings.INSTALLED_APPS:
    if 'product' in app or 'store' in app:
        print(f"  - {app}")

# Проверяем базу данных
print(f"\n🗄️ Проверка базы данных:")
from django.apps import apps

for model in apps.get_models():
    if 'Product' in model.__name__:
        print(f"  - {model.__name__} в {model._meta.app_label}")
        print(f"    Таблица: {model._meta.db_table}")
        print(f"    Поля: {[f.name for f in model._meta.fields]}")