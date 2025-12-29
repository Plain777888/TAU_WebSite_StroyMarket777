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
# DATABASES = {
#     'default': env.db(),
#     'OPTIONS': {
#         'sslmode': 'require',
#         'connect_timeout': 10,# Важно для Supabase!
#     }
#     # читает DATABASE_URL из .env
# }
BASE_DIR = Path(__file__).resolve().parent.parent

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
MEDIA_ROOT = BASE_DIR / 'media'

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

CART_SESSION_ID = 'cart'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

import os
from django.core.management import execute_from_command_line

# Проверяем, что мы в среде выполнения (не во время сборки)
if os.environ.get('RUN_MAIN') or not os.environ.get('WERKZEUG_RUN_MAIN'):
    try:
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # Параметры суперпользователя (ИЗМЕНИТЕ ПАРОЛЬ!)
        username = 'admin'
        email = 'admin@example.com'
        password = 'dlfsmlkdmalmdKFSLSL123456!klsmfkmdaasft'  # ОБЯЗАТЕЛЬНО ЗАМЕНИТЕ НА СВОЙ

        # Создаём, если не существует
        if not User.objects.filter(username=username).exists():
            print('🔄 Создание суперпользователя...')
            User.objects.create_superuser(username=username, email=email, password=password)
            print('✅ Суперпользователь создан!')
        else:
            print('ℹ️ Суперпользователь уже существует.')

    except Exception as e:
        print(f'⚠️ Не удалось создать суперпользователя: {e}')