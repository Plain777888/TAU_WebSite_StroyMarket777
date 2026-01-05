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
    categories = Category.objects.all()
    products = Product.objects.filter(category=category, available=True)

    # Пагинация
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'products': page_obj,
        'categories': categories,
    }
    return render(request, 'store/category.html', context)


def product_detail(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug, available=True)
    product_images = product.images.all()
    categories = Category.objects.all()
    related_products = Product.objects.filter(
        category=product.category, available=True
    ).exclude(id=product.id)[:4]

    context = {
        'product': product,
        'product_images': product_images,
        'related_products': related_products,
        'categories': categories,
    }
    return render(request, 'store/product_detail.html', context)


def search(request):
    categories = Category.objects.all()
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
        'categories': categories,
    }
    return render(request, 'store/search.html', context)


def cart_view(request):
    cart_items = Cart.objects.filter(session_key=request.session.session_key)
    total_price = sum(item.total_price for item in cart_items)
    categories = Category.objects.all()



    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'categories': categories,
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

#@login_required
def checkout(request):
    categories = Category.objects.all()
    cart_items = Cart.objects.filter(session_key=request.session.session_key)
    # cart = get_object_or_404(Cart, user=request.user)
    delivery_cost_fin = 0
    # context = {
    #     'categories': categories,
    # }

    if not cart_items.exists():
        messages.warning(request, 'Ваша корзина пуста')
        return redirect('store:cart')

    if request.method == 'POST':
        form = OrderForm(request.POST)

        if form.is_valid():


            delivery_type = request.POST.get('delivery_type')

            payment_type = request.POST.get('payment_type')
            if delivery_type == 'courier':
                # Доставка курьером
                address_street = request.POST.get('address_street')
                address_apartment = request.POST.get('address_apartment', '')
                address_entrance = request.POST.get('address_entrance', '')
                address_floor = request.POST.get('address_floor', '')
                address_comment = request.POST.get('address_comment', '')

                # Формируем полный адрес
                full_address = address_street
                if address_apartment:
                    full_address += f', кв. {address_apartment}'
                if address_entrance:
                    full_address += f', подъезд {address_entrance}'
                if address_floor:
                    full_address += f', этаж {address_floor}'
                if address_comment:
                    full_address += f' ({address_comment})'

                delivery_cost_fin += 300
                delivery_address = full_address
                pickup_point = None

            else:  # pickup
                # Самовывоз
                pickup_point_id = request.POST.get('pickup_point')
                # Здесь можно получить информацию о пункте выдачи из базы
                pickup_points = {
                    '1': 'ул. Ленина, 10, ежедневно 9:00-21:00',
                    '2': 'ул. Промышленная, 25, пн-пт 10:00-19:00',
                    '3': 'пр. Строителей, 15, ТЦ "Строймаркет", 3 этаж',
                }

                delivery_cost_fin += 0
                pickup_point = pickup_points.get(pickup_point_id, 'Не указан')
                delivery_address = pickup_point


            order = form.save()
            # Рассчитываем итоговую сумму
            # total_amount = cart.total_price + delivery_cost
            # Создаем элементы заказа

            for cart_item in cart_items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    price=cart_item.product.price,
                    quantity=cart_item.quantity
                )

            # Очищаем корзину
            cart_items.delete()

            messages.success(request, 'Ваш заказ успешно оформлен!')
            return redirect('store:index',)

    else:

        form = OrderForm()

    total_price = sum(item.total_price for item in cart_items)+delivery_cost_fin


    context = {
        'form': form,
        'cart_items': cart_items,
        'total_price': total_price,
        'categories':categories,


    }
    return render(request, 'store/checkout.html', context)


# Регистрация
def register_view(request):
    categories = Category.objects.all()
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

    return render(request, 'store/auth/register.html', {'form': form,'categories': categories})


# Авторизация
def login_view(request):
    categories = Category.objects.all()
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

    return render(request, 'store/auth/login.html', {'form': form,'categories': categories})


# Выход
def logout_view(request):
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы.')
    return redirect('store:index')


# Личный кабинет
@login_required
def profile_view(request):
    user = request.user
    categories = Category.objects.all()
    orders = Order.objects.filter(email=user.email).order_by('-created')[:10]

    return render(request, 'store/auth/profile.html', {
        'user': user,
        'orders': orders,
        'categories': categories,
    })


# Редактирование профиля
@login_required
def edit_profile_view(request):
    categories = Category.objects.all()
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
        'categories': categories,
    })


# Изменение пароля
@login_required
def change_password_view(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Пароль успешно изменен!')
            return redirect('store:profile')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'store/auth/change_password.html', {'form': form,'categories': categories})


# История заказов
@login_required
def order_history_view(request):
    categories = Category.objects.all()
    orders = Order.objects.filter(email=request.user.email).order_by('-created')

    return render(request, 'store/auth/order_history.html', {'orders': orders, 'categories': categories})


# Детали заказа
@login_required
def order_detail_view(request, order_id):
    categories = Category.objects.all()
    order = get_object_or_404(Order, id=order_id, email=request.user.email)

    return render(request, 'store/auth/order_detail.html', {'order': order,'categories':categories})


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


from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

def about(request):
    categories = Category.objects.all()
    """Страница О нас"""
    return render(request, 'store/about.html',context={'categories': categories})

def otzov(request):
    categories = Category.objects.all()
    """Страница отзывов"""
    return render(request, 'store/otzov.html',context={'categories': categories})


@csrf_exempt
def add_review(request):
    """Добавление отзыва (API endpoint)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Здесь вы можете сохранить отзыв в базу данных
            # Например:
            # from .models import Review
            # review = Review.objects.create(
            #     name=data.get('name'),
            #     email=data.get('email'),
            #     rating=data.get('rating'),
            #     title=data.get('title'),
            #     text=data.get('review'),
            #     product=data.get('product', '')
            # )

            # Пока просто возвращаем успешный ответ
            return JsonResponse({'status': 'success', 'message': 'Отзыв успешно добавлен'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Неверный метод запроса'}, status=405)


def get_reviews(request):
    """Получение всех отзывов (API endpoint)"""
    # Здесь вы можете получать отзывы из базы данных
    # Например:
    # from .models import Review
    # reviews = Review.objects.all().order_by('-created_at')
    # reviews_data = [{
    #     'id': r.id,
    #     'name': r.name,
    #     'rating': r.rating,
    #     'title': r.title,
    #     'review': r.text,
    #     'product': r.product,
    #     'date': r.created_at.strftime('%Y-%m-%d')
    # } for r in reviews]

    # Пока возвращаем тестовые данные
    reviews_data = [
        {
            'id': 1,
            'name': 'Андрей Петров',
            'rating': 5,
            'title': 'Отличный перфоратор для домашнего ремонта',
            'review': 'Приобрел этот перфоратор для ремонта в квартире. Работает отлично, мощность достаточная для бетонных стен.',
            'product': 'Перфоратор Bosch GBH 2-26 DFR',
            'date': '2023-10-15'
        },
        {
            'id': 2,
            'name': 'Ирина Смирнова',
            'rating': 4,
            'title': 'Хорошая краска, но цвет немного отличается',
            'review': 'Краска качественная, хорошо ложится, практически без запаха.',
            'product': 'Краска Dulux для стен',
            'date': '2023-10-10'
        }
    ]

    return JsonResponse({'reviews': reviews_data,'categories':categories})