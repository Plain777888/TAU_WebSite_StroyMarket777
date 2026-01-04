# supabase_storage.py
import os
from urllib.parse import urljoin
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from django.conf import settings
from supabase import create_client
import uuid


@deconstructible
class SupabaseStorage(Storage):
    """Кастомный storage для работы с Supabase"""

    def __init__(self, option=None):
        self.supabase = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        self.bucket_name = getattr(settings, 'SUPABASE_BUCKET', 'public')

    def _open(self, name, mode='rb'):
        # Для чтения файлов
        from io import BytesIO
        try:
            response = self.supabase.storage.from_(self.bucket_name).download(name)
            if hasattr(response, 'read'):
                return response
            return BytesIO(response)
        except Exception as e:
            print(f"Error opening file {name}: {e}")
            return None

    def _save(self, name, content):
        # Если name уже содержит путь, используем его, иначе генерируем новый
        if not name:
            ext = os.path.splitext(content.name)[1]
            name = f"products/{uuid.uuid4()}{ext}"

        # Проверяем, содержит ли name путь к папке
        if 'products/' not in name:
            name = f"products/{name}"

        # Читаем содержимое файла
        if hasattr(content, 'read'):
            file_content = content.read()
        else:
            file_content = content

        # Определяем content-type
        content_type = self._get_content_type(name)

        # Загружаем в Supabase
        try:
            # Сначала проверяем, существует ли файл
            try:
                # Пытаемся удалить старый файл, если он существует
                self.supabase.storage.from_(self.bucket_name).remove([name])
            except:
                pass  # Файл не существует, это нормально

            # Загружаем новый файл
            result = self.supabase.storage.from_(self.bucket_name).upload(
                name,
                file_content,
                {"content-type": content_type}
            )

            print(f"File uploaded successfully: {name}")
            return name

        except Exception as e:
            print(f"Error uploading file {name} to Supabase: {e}")
            raise

    def delete(self, name):
        try:
            self.supabase.storage.from_(self.bucket_name).remove([name])
        except Exception as e:
            print(f"Error deleting file {name}: {e}")

    def exists(self, name):
        try:
            # Получаем список файлов в bucket
            files = self.supabase.storage.from_(self.bucket_name).list()
            # Ищем файл по имени
            for file_info in files:
                if file_info.get('name') == name:
                    return True
            return False
        except Exception as e:
            print(f"Error checking existence of {name}: {e}")
            return False

    def url(self, name):
        if not name:
            return ''
        return f"{settings.SUPABASE_URL}/storage/v1/object/public/{self.bucket_name}/{name}"

    def _get_content_type(self, filename):
        """Определяем content-type по расширению файла"""
        ext = os.path.splitext(filename)[1].lower()
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.pdf': 'application/pdf',
        }
        return content_types.get(ext, 'application/octet-stream')

    def get_available_name(self, name, max_length=None):
        """Генерируем уникальное имя файла"""
        dir_name, file_name = os.path.split(name)
        file_root, file_ext = os.path.splitext(file_name)

        # Если файл уже существует, генерируем новое имя
        while self.exists(name):
            name = os.path.join(
                dir_name,
                f"{file_root}_{uuid.uuid4().hex[:8]}{file_ext}"
            )

        return name

    def size(self, name):
        try:
            # Получаем метаданные файла
            files = self.supabase.storage.from_(self.bucket_name).list()
            for file_info in files:
                if file_info.get('name') == name:
                    return file_info.get('metadata', {}).get('size', 0)
            return 0
        except:
            return 0