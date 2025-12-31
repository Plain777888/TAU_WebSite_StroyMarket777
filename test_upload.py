# test_admin_fix.py
import os
import django
import sys
from PIL import Image
from io import BytesIO

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'construction_store.settings')
django.setup()

from products.models import Product
from django.core.files.uploadedfile import SimpleUploadedFile

print("=" * 60)
print("ТЕСТ: Исправление проблемы с админкой")
print("=" * 60)

# Создаем реальное изображение
image = Image.new('RGB', (400, 300), color='green')
img_io = BytesIO()
image.save(img_io, 'JPEG', quality=90)
img_io.seek(0)

# Создаем файл как в админке
test_file = SimpleUploadedFile(
    'test_fix.jpg',
    img_io.getvalue(),
    content_type='image/jpeg'
)

# Тест 1: Создание через objects.create()
print("\n1. Тест: Product.objects.create()")
try:
    p1 = Product.objects.create(
        name="ТЕСТ FIX 1",
        price=1000,
        image_file=test_file
    )
    print(f"   Результат: ID={p1.id}, URL={p1.image_url}")
    print(f"   image_file после save: {p1.image_file}")
except Exception as e:
    print(f"   ОШИБКА: {e}")

# Тест 2: Создание и вызов save()
print("\n2. Тест: Создание + ручной save()")
try:
    test_file2 = SimpleUploadedFile(
        'test_fix2.jpg',
        Image.new('RGB', (200, 200), color='blue').tobytes(),
        content_type='image/jpeg'
    )

    p2 = Product(name="ТЕСТ FIX 2", price=2000)
    p2.image_file = test_file2
    p2.save()

    print(f"   Результат: ID={p2.id}, URL={p2.image_url}")
    print(f"   image_file после save: {p2.image_file}")

except Exception as e:
    print(f"   ОШИБКА: {e}")

# Проверяем все товары
print("\n" + "=" * 60)
print("ВСЕ ТОВАРЫ В БАЗЕ:")
for p in Product.objects.all():
    print(f"- {p.name}: {p.image_url or 'НЕТ URL'}")