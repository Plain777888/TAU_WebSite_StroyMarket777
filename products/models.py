# products/models.py
import os
from django.db import models
from django.core.files.storage import FileSystemStorage
from supabase import create_client, Client
from io import BytesIO
from PIL import Image
import uuid

import logging
logger = logging.getLogger(__name__)

# Временное локальное хранилище
temp_storage = FileSystemStorage(location='media/temp')


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=10, default='шт')
    stock = models.IntegerField(default=0)
    image = models.CharField(max_length=500, blank=True, null=True)

    # Поле для временного хранения файла
    image_file = models.ImageField(
        upload_to='temp_products/',
        storage=temp_storage,
        blank=True,
        null=True
    )

    # Поле для хранения URL Supabase
    image_url = models.URLField(max_length=500, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # ВАЖНО: Читаем файл ДО вызова upload_to_supabase
        file_content = None
        file_name = None

        if self.image_file and hasattr(self.image_file, 'file'):
            print(f"SAVE: Найден файл {self.image_file.name}")

            # 1. Сохраняем имя и читаем содержимое
            file_name = self.image_file.name
            original_file = self.image_file.file
            original_file.seek(0)
            file_content = original_file.read()
            original_file.seek(0)  # Возвращаемся в начало для возможного повторного чтения

            # 2. Загружаем в Supabase
            supabase_url = self.upload_to_supabase()

            if supabase_url:
                # Сохраняем URL
                self.image_url = supabase_url
                print(f"SAVE: URL сохранен: {supabase_url}")

        # Вызываем родительский save
        super().save(*args, **kwargs)

        # 3. ПОСЛЕ сохранения очищаем поле (если загрузка удалась)
        if self.image_file and self.image_url and hasattr(self.image_file, 'file'):
            try:
                self.image_file.delete(save=False)
                # Не очищаем self.image_file = None, чтобы не ломать админку
                # Вместо этого обновим запись без файла
                Product.objects.filter(id=self.id).update(image_file=None)
            except:
                pass

    def upload_to_supabase(self):
        """Загрузка изображения в Supabase Storage"""
        try:
            # Проверяем, есть ли файл
            if not self.image_file or not hasattr(self.image_file, 'file'):
                print("Нет файла для загрузки")
                return None

            # Инициализация клиента Supabase
            supabase: Client = create_client(
                os.environ.get('SUPABASE_URL'),
                os.environ.get('SUPABASE_SERVICE_KEY')
            )

            # Получаем оригинальный файл
            original_file = self.image_file.file

            # Генерируем уникальное имя файла
            original_name = self.image_file.name
            file_extension = os.path.splitext(original_name)[1].lower()
            unique_filename = f"{uuid.uuid4()}{file_extension}"

            # Получаем content_type (варианты)
            if hasattr(original_file, 'content_type'):
                content_type = original_file.content_type
            elif hasattr(self.image_file, 'content_type'):
                content_type = self.image_file.content_type
            else:
                # Определяем по расширению
                if file_extension in ['.jpg', '.jpeg']:
                    content_type = 'image/jpeg'
                elif file_extension == '.png':
                    content_type = 'image/png'
                elif file_extension == '.webp':
                    content_type = 'image/webp'
                else:
                    content_type = 'application/octet-stream'

            print(f"Content-Type: {content_type}")

            # Читаем файл
            original_file.seek(0)  # Важно: переходим в начало файла
            file_content = original_file.read()

            # Оптимизируем изображение (опционально)
            if file_extension in ['.jpg', '.jpeg', '.png', '.webp']:
                optimized_content = self.optimize_image(file_content, file_extension)
                if optimized_content:
                    file_content = optimized_content

            # Загружаем в Supabase Storage
            print(f"Загружаем файл {unique_filename} ({len(file_content)} bytes)...")

            response = supabase.storage.from_('products').upload(
                unique_filename,
                file_content,
                {
                    "content-type": content_type,
                    "cache-control": "public, max-age=31536000"
                }
            )

            # Получаем публичный URL
            public_url = supabase.storage.from_('products').get_public_url(unique_filename)

            print(f"✅ Файл загружен в Supabase: {public_url}")
            return public_url

        except Exception as e:
            print(f"❌ Ошибка загрузки в Supabase: {e}")
            import traceback
            traceback.print_exc()
            return None

    def optimize_image(self, file_content, extension):
        """Оптимизация изображения перед загрузкой"""
        try:
            img = Image.open(BytesIO(file_content))

            # Конвертируем в RGB если нужно
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # Изменяем размер если слишком большой
            max_size = (1200, 1200)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Сохраняем в BytesIO
            output = BytesIO()

            if extension in ['.jpg', '.jpeg']:
                img.save(output, format='JPEG', quality=85, optimize=True)
            elif extension == '.png':
                img.save(output, format='PNG', optimize=True)
            elif extension == '.webp':
                img.save(output, format='WEBP', quality=85)
            else:
                return None

            output.seek(0)
            return output.read()

        except Exception as e:
            print(f"Ошибка оптимизации: {e}")
            return None

    @property
    def image(self):
        """Возвращает URL изображения (Supabase или локальный)"""
        if self.image_url:
            return self.image_url
        elif self.image_file:
            return self.image_file.url
        return None

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"