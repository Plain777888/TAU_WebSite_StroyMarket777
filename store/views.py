from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib import messages
from .models import Category, Product, Cart, Order, OrderItem
from .forms import OrderForm

from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from .models import Category, Product, Cart, Order, OrderItem, UserProfile
#from .forms import RegisterForm, LoginForm, ProfileForm, UserProfileForm, OrderForm, PasswordChangeForm
from .forms import RegisterForm, LoginForm, ProfileForm, UserProfileForm, OrderForm
from django.contrib.auth.forms import PasswordChangeForm  # Импортируем из Django

def index(request):
    categories = Category.objects.all()
    featured_products = Product.objects.filter(available=True)[:8]
    new_products = Product.objects.filter(available=True).order_by('-created')[:8]

    context = {
        'categories': categories,
        'featured_products': featured_products,
        'new_products': new_products,
    }
    return render(request, 'store/index.html', context)


def category_view(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    products = Product.objects.filter(category=category, available=True)

    # Пагинация
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'products': page_obj,
    }
    return render(request, 'store/category.html', context)


def product_detail(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug, available=True)
    related_products = Product.objects.filter(
        category=product.category, available=True
    ).exclude(id=product.id)[:4]

    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'store/product_detail.html', context)


def search(request):
    query = request.GET.get('q', '')
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__icontains=query) |
            Q(material__icontains=query),
            available=True
        )
    else:
        products = Product.objects.filter(available=True)

    # Пагинация
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'query': query,
        'products': page_obj,
    }
    return render(request, 'store/search.html', context)


def cart_view(request):
    cart_items = Cart.objects.filter(session_key=request.session.session_key)
    total_price = sum(item.total_price for item in cart_items)

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'store/cart.html', context)


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)

    if not request.session.session_key:
        request.session.create()

    cart_item, created = Cart.objects.get_or_create(
        session_key=request.session.session_key,
        product=product,
        defaults={'quantity': 1}
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    messages.success(request, f'Товар "{product.name}" добавлен в корзину')
    return redirect('store:cart')


def update_cart(request, cart_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(Cart, id=cart_id)
        quantity = int(request.POST.get('quantity', 1))

        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()

        messages.success(request, 'Корзина обновлена')

    return redirect('store:cart')


def remove_from_cart(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id)
    cart_item.delete()
    messages.success(request, 'Товар удален из корзины')
    return redirect('store:cart')


def checkout(request):
    cart_items = Cart.objects.filter(session_key=request.session.session_key)

    if not cart_items.exists():
        messages.warning(request, 'Ваша корзина пуста')
        return redirect('store:cart')

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save()

            # Создаем элементы заказа
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    price=cart_item.product.price,
                    quantity=cart_item.quantity
                )

            # Очищаем корзину
            cart_items.delete()

            messages.success(request, 'Ваш заказ успешно оформлен!')
            return redirect('store:index')
    else:
        form = OrderForm()

    total_price = sum(item.total_price for item in cart_items)

    context = {
        'form': form,
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'store/checkout.html', context)


# Регистрация
def register_view(request):
    if request.user.is_authenticated:
        return redirect('store:index')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно! Добро пожаловать!')
            return redirect('store:index')
    else:
        form = RegisterForm()

    return render(request, 'store/auth/register.html', {'form': form})


# Авторизация
def login_view(request):
    if request.user.is_authenticated:
        return redirect('store:index')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {username}!')

                # Перенаправляем на следующую страницу или на главную
                next_page = request.GET.get('next', 'store:index')
                return redirect(next_page)
    else:
        form = LoginForm()

    return render(request, 'store/auth/login.html', {'form': form})


# Выход
def logout_view(request):
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы.')
    return redirect('store:index')


# Личный кабинет
@login_required
def profile_view(request):
    user = request.user
    orders = Order.objects.filter(email=user.email).order_by('-created')[:10]

    return render(request, 'store/auth/profile.html', {
        'user': user,
        'orders': orders,
    })


# Редактирование профиля
@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        user_form = ProfileForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=request.user.userprofile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('store:profile')
    else:
        user_form = ProfileForm(instance=request.user)
        profile_form = UserProfileForm(instance=request.user.userprofile)

    return render(request, 'store/auth/edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })


# Изменение пароля
@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Пароль успешно изменен!')
            return redirect('store:profile')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'store/auth/change_password.html', {'form': form})


# История заказов
@login_required
def order_history_view(request):
    orders = Order.objects.filter(email=request.user.email).order_by('-created')

    return render(request, 'store/auth/order_history.html', {'orders': orders})


# Детали заказа
@login_required
def order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, email=request.user.email)

    return render(request, 'store/auth/order_detail.html', {'order': order})


# В views.py добавьте:
from django.http import HttpResponse
from django.conf import settings


def test_image_url(request):
    """Простая страница для теста изображения"""
    from .models import Product

    product = Product.objects.first()
    if not product:
        return HttpResponse("Нет товаров в базе")

    html = f"""
    <html>
    <head><title>Тест изображения</title></head>
    <body>
        <h1>Тест изображения для: {product.name}</h1>

        <h3>Данные:</h3>
        <pre>
        Поле image: {product.image}
        SUPABASE_URL: {settings.SUPABASE_URL}
        </pre>

        <h3>Сформированный URL:</h3>
        <p><code>{product.get_main_image()}</code></p>

        <h3>Попробуйте открыть вручную:</h3>
        <p><a href="{product.get_main_image()}" target="_blank">
            {product.get_main_image()}
        </a></p>

        <h3>Тестовое изображение:</h3>
        <img src="{product.get_main_image()}" 
             style="max-width: 400px; border: 2px solid red;"
             onerror="alert('Ошибка загрузки изображения!')">

        <hr>
        <p>Если изображение не загружается, проверьте:
        <ol>
            <li>Правильность SUPABASE_URL в settings.py</li>
            <li>Права доступа в Supabase Storage</li>
            <li>Что файл действительно существует по указанному пути</li>
        </ol>
        </p>
    </body>
    </html>
    """

    return HttpResponse(html)