from django.http import HttpResponse
from django.contrib.auth.decorators import user_passes_test
from store.models import Category, Product  # замените на ваши модели


@user_passes_test(lambda u: u.is_superuser)
def check_data(request):
    categories = Category.objects.all()
    products = Product.objects.all()

    output = f"""
    <h1>Проверка данных</h1>
    <p>Категорий: {categories.count()}</p>
    <p>Товаров: {products.count()}</p>

    <h2>Категории:</h2>
    <ul>
    """
    for cat in categories:
        output += f"<li>{cat.name} (ID: {cat.id})</li>"

    output += "</ul>"

    return HttpResponse(output)


# views.py - добавьте эту функцию
from django.http import HttpResponse
from django.contrib.auth import get_user_model
import json


def reset_admin_password(request):
    """ВРЕМЕННАЯ функция для сброса пароля админа"""
    # Простая защита - проверка секретного ключа
    secret_key = request.GET.get('key', '')
    if secret_key != 'dlskfkdsfm31293i02409DSKJFDN!':  # ⚠️ ЗАМЕНИТЕ
        return HttpResponse('Неверный ключ', status=403)

    User = get_user_model()
    try:
        user = User.objects.get(username='admin')
        new_password = 'mafdogmldkmflskmfafmoiewSJNSKFJSF312312!'  # ⚠️ ЗАМЕНИТЕ
        user.set_password(new_password)
        user.save()

        return HttpResponse(json.dumps({
            'success': True,
            'message': f'Пароль сброшен. Новый: {new_password}'
        }))
    except User.DoesNotExist:
        return HttpResponse(json.dumps({
            'success': False,
            'message': 'Пользователь admin не найден'
        }))


import os
from django.http import JsonResponse


def check_fixtures(request):
    """Проверка наличия файлов с данными"""
    fixtures_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(fixtures_dir)

    files_to_check = [
        'unicode_fixed_data.json',
        'data.json',
        'clean_data.json',
        'store_data.json',
        'test_data.json'
    ]

    found_files = {}
    for filename in files_to_check:
        filepath = os.path.join(project_root, filename)
        exists = os.path.exists(filepath)
        found_files[filename] = {
            'exists': exists,
            'size': os.path.getsize(filepath) if exists else 0
        }

    return JsonResponse(found_files)