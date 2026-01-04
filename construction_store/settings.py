import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv
import environ

env = environ.Env()
environ.Env.read_env()

# Загружаем переменные из .env
load_dotenv()
# URL для перенаправления после входа/выхода
LOGIN_REDIRECT_URL = '/profile/'
LOGOUT_REDIRECT_URL = '/'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres.jfzkqlynhzlzbuqihbxj',
        'PASSWORD': os.getenv('DB_PASSWORD'),  # Из переменных окружения
        'HOST': 'aws-1-eu-west-1.pooler.supabase.com',
        'PORT': '6543',
        'OPTIONS': {'sslmode': 'require'},
    }
}
# Supabase настройки
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')  # для записи
SUPABASE_BUCKET = "products"  # Имя bucket в Supabase Storage

# Настройки файлов
DEFAULT_FILE_STORAGE = 'supabase_storage.SupabaseStorage'



LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'DEBUG',
    },
    'loggers': {
        'products': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
# DATABASES = {
#     'default': env.db(),
#     'OPTIONS': {
#         'sslmode': 'require',
#         'connect_timeout': 10,# Важно для Supabase!
#     }
#     # читает DATABASE_URL из .env
# }
BASE_DIR = Path(__file__).resolve().parent.parent

# URL для медиа файлов
MEDIA_URL = f'{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'temp_media')

# # Проверяем, есть ли переменная DATABASE_URL (для продакшена)
# if os.environ.get('DATABASE_URL'):
#     # Режим продакшена - используем PostgreSQL через DATABASE_URL
#     DATABASES = {
#         'default': dj_database_url.config(
#             default=os.environ.get('DATABASE_URL'),
#             conn_max_age=600
#         )
#     }
# else:
#     # Режим разработки - используем SQLite локально
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.sqlite3',
#             'NAME': BASE_DIR / 'db.sqlite3',
#         }
#     }
# URL для входа
LOGIN_URL = '/login/'

# Настройки email (для сброса пароля)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Для разработки
# Для продакшена:
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'ваш_email@gmail.com'
# EMAIL_HOST_PASSWORD = 'ваш_пароль'

#BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'ваш-секретный-ключ'

DEBUG = True

ALLOWED_HOSTS = ['tau-website-stroymarket777.onrender.com', '127.0.0.1', 'localhost']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'store',
    'crispy_forms',
    'crispy_bootstrap5',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'construction_store.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'store.context_processors.cart_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'construction_store.wsgi.application'



AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
#MEDIA_ROOT = BASE_DIR / 'media'

# Bucket name в Supabase Storage
SUPABASE_STORAGE_BUCKET = 'products'

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

CART_SESSION_ID = 'cart'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Добавьте этот код в конец settings.py или в файл, который импортируется при запуске
import os
import sys

# # Проверяем, что это не команда управления Django (migrate, collectstatic и т.д.)
# # и не выполнение тестов
# if ('RUN_MAIN' in os.environ or not 'WERKZEUG_RUN_MAIN' in os.environ) and 'test' not in sys.argv:
#     try:
#         from django.contrib.auth import get_user_model
#         from django.db import IntegrityError
#
#         User = get_user_model()
#
#         # Параметры суперпользователя
#         username = 'admin'
#         email = 'admin@example.com'
#         password = 'mafdogmldkmflskmfafmoiewSJNSKFJSF312312!'  # ⚠️ ОБЯЗАТЕЛЬНО ЗАМЕНИТЕ!
#
#         # Пытаемся создать только если не существует
#         if not User.objects.filter(username=username).exists():
#             print('🔄 Создание суперпользователя...')
#             try:
#                 User.objects.create_superuser(username=username, email=email, password=password)
#                 print(f'✅ Суперпользователь "{username}" создан!')
#             except IntegrityError:
#                 print(f'ℹ️ Пользователь "{username}" уже существует (IntegrityError)')
#         else:
#             print(f'ℹ️ Суперпользователь "{username}" уже существует.')
#
#     except Exception as e:
#         # Игнорируем ошибки, связанные с недоступностью базы данных при старте
#         if 'database' in str(e).lower() or 'connection' in str(e).lower():
#             print('⚠️ База данных временно недоступна, пропускаем создание пользователя')
#         else:
#             print(f'⚠️ Ошибка при проверке/создании суперпользователя: {e}')

# === АВТОМАТИЧЕСКАЯ НАСТРОЙКА ПРИ ЗАПУСКЕ ===
import os
import sys
import time
import logging
import threading

logger = logging.getLogger(__name__)



def startup_tasks():
    """Задачи, выполняемые после полного запуска Django"""
    time.sleep(3)  # Ждем полной инициализации Django

    try:
        print("🚀 Запуск startup_tasks...")

        # 1. Проверяем/создаем суперпользователя
        from django.contrib.auth import get_user_model
        User = get_user_model()

        username = 'admin'
        email = 'admin@example.com'
        password = 'mafdogmldkmflskmfafmoiewSJNSKFJSF312312!!'  # ⚠️ ЗАМЕНИТЕ!

        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email, 'is_staff': True, 'is_superuser': True}
        )

        if created:
            user.set_password(password)
            user.save()
            print(f'✅ Создан суперпользователь "{username}"')
        else:
            # Сбрасываем пароль на известный
            user.set_password(password)
            user.save()
            print(f'✅ Пароль для "{username}" сброшен')

        # 2. Загружаем данные магазина
        from django.core.management import call_command
        from store.models import Category, Product

        # Проверяем, есть ли уже данные
        if Category.objects.count() == 0 or Product.objects.count() == 0:
            print("📦 Загружаю данные магазина...")

            # Пробуем разные файлы
            fixtures = ['unicode_fixed_data.json', 'store_data.json', 'data.json']
            for fixture in fixtures:
                if os.path.exists(fixture):
                    try:
                        call_command('loaddata', fixture)
                        print(f"✅ Данные загружены из {fixture}")
                        break
                    except Exception as e:
                        print(f"❌ Ошибка загрузки {fixture}: {e}")

        # 3. Выводим итоги
        print("\n📊 ИТОГО В БАЗЕ:")
        print(f"   Категорий: {Category.objects.count()}")
        print(f"   Товаров: {Product.objects.count()}")
        print(f"   Пользователей: {User.objects.count()}")
        print(f"\n🔑 ДАННЫЕ ДЛЯ ВХОДА В АДМИНКУ:")
        print(f"   URL: https://tau-website-stroymarket777.onrender.com/admin/")
        print(f"   Логин: {username}")
        print(f"   Пароль: {password}")

    except Exception as e:
        print(f"⚠️ Ошибка в startup_tasks: {e}")


# Запускаем в отдельном потоке при старте
if os.environ.get('RENDER'):
    print("🔄 RENDER detected, scheduling startup tasks...")
    thread = threading.Thread(target=startup_tasks)
    thread.daemon = True
    thread.start()