# custom_dump_fixed.py
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'construction_store.settings')
django.setup()

from django.core import serializers
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from store.models import *  # ваши модели из приложения store

print("Экспорт данных с поддержкой Unicode...")

# Собираем все данные
all_data = []

# 1. Auth данные
print("Экспорт пользователей...")
all_data.extend(json.loads(serializers.serialize("json", User.objects.all())))

print("Экспорт групп...")
all_data.extend(json.loads(serializers.serialize("json", Group.objects.all())))

print("Экспорт разрешений...")
all_data.extend(json.loads(serializers.serialize("json", Permission.objects.all())))

print("Экспорт типов контента...")
all_data.extend(json.loads(serializers.serialize("json", ContentType.objects.all())))

# 2. Ваши модели из store
try:
    print("Экспорт категорий...")
    all_data.extend(json.loads(serializers.serialize("json", Category.objects.all())))
except Exception as e:
    print(f"Ошибка экспорта категорий: {e}")

try:
    print("Экспорт продуктов...")
    all_data.extend(json.loads(serializers.serialize("json", Product.objects.all())))
except Exception as e:
    print(f"Ошибка экспорта продуктов: {e}")

try:
    print("Экспорт изображений продуктов...")
    all_data.extend(json.loads(serializers.serialize("json", ProductImage.objects.all())))
except Exception as e:
    print(f"Ошибка экспорта изображений: {e}")

try:
    print("Экспорт профилей пользователей...")
    all_data.extend(json.loads(serializers.serialize("json", UserProfile.objects.all())))
except Exception as e:
    print(f"Ошибка экспорта профилей: {e}")

# Сохраняем с поддержкой Unicode
with open('unicode_fixed_data.json', 'w', encoding='utf-8') as f:
    json.dump(all_data, f, indent=2, ensure_ascii=False)

print(f"✅ Файл создан: unicode_fixed_data.json")
print(f"✅ Всего записей: {len(all_data)}")