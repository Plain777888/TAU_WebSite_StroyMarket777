# test_upload_fixed2.py
import os
import django
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'construction_store.settings')
django.setup()

from products.models import Product
from django.core.files.uploadedfile import SimpleUploadedFile

# Создаем БОЛЬШОЙ тестовый файл (имитация реального изображения)
# PIL не сможет обработать слишком маленький файл
jpg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00'  # Заголовок JPEG
test_content = jpg_header + b'x' * 10000  # Делаем файл побольше

test_file = SimpleUploadedFile(
    'test_image.jpg',
    test_content,
    content_type='image/jpeg'
)

# Тест 1: Сохранение через create
print("=" * 50)
print("ТЕСТ 1: Создание нового товара")
print("=" * 50)

try:
    product = Product.objects.create(
        name="ТЕСТОВЫЙ ТОВАР 1",
        price=999.99,
        image_file=test_file
    )

    print(f"Товар ID: {product.id}")
    print(f"Имя файла: {product.image_file.name}")
    print(f"URL в БД: {product.image_url}")

    if product.image_url:
        print(f"✅ УСПЕХ! URL: {product.image_url}")
    else:
        print("❌ ОШИБКА: URL не создан")

except Exception as e:
    print(f"❌ ОШИБКА при создании: {e}")
    import traceback

    traceback.print_exc()

# Тест 2: Создание объекта и вызов save вручную
print("\n" + "=" * 50)
print("ТЕСТ 2: Ручной вызов save()")
print("=" * 50)

try:
    test_file2 = SimpleUploadedFile(
        'test2.jpg',
        jpg_header + b'y' * 10000,
        content_type='image/jpeg'
    )

    product2 = Product(
        name="ТЕСТОВЫЙ ТОВАР 2",
        price=1999.99,
    )
    product2.image_file = test_file2
    product2.save()  # Вызываем save вручную

    print(f"Товар ID: {product2.id}")
    print(f"URL в БД: {product2.image_url}")

except Exception as e:
    print(f"❌ ОШИБКА: {e}")
    import traceback

    traceback.print_exc()

# Проверка всех товаров в БД
print("\n" + "=" * 50)
print("ВСЕ ТОВАРЫ В БАЗЕ ДАННЫХ:")
print("=" * 50)

for p in Product.objects.all():
    print(f"- {p.name}: {p.image_url or 'Нет изображения'}")