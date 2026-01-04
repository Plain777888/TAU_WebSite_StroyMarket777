# test_supabase.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'construction_store.settings')
django.setup()

from supabase import create_client
from django.conf import settings


def test_supabase_connection():
    print("Testing Supabase connection...")

    # Инициализация клиента
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

    # Проверка соединения
    try:
        # Получаем список buckets
        buckets = supabase.storage.list_buckets()
        print(f"Available buckets: {buckets}")

        # Проверяем доступ к нужному bucket
        response = supabase.storage.from_('products').list()
        print(f"Files in 'products' bucket: {response}")

        print("✓ Supabase connection successful!")
        return True
    except Exception as e:
        print(f"✗ Error connecting to Supabase: {e}")
        return False


if __name__ == "__main__":
    test_supabase_connection()