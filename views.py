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