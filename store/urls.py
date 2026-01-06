from django.urls import path
from . import views

from django.contrib.auth import views as auth_views

app_name = 'store'

urlpatterns = [
    path('', views.index, name='index'),
    path('category/<slug:category_slug>/', views.category_view, name='category'),
    path('product/<slug:product_slug>/', views.product_detail, name='product_detail'),
    path('search/', views.search, name='search'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:cart_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:cart_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),

    path('otzov/', views.otzov, name='otzov'),
    path('api/add-review/', views.add_review, name='add_review'),
    path('api/get-reviews/', views.get_reviews, name='get_reviews'),

    path('about/', views.about, name='about'),
    path('otzov/', views.otzov, name='otzov'),

    path('promotions/', views.promotions_list, name='promotions'),
    path('promotions/<int:promotion_id>/', views.promotion_detail, name='promotion_detail'),
    path('promotions/products/', views.products_on_promotion, name='products_on_promotion'),
    path('api/promotions/', views.api_promotions, name='api_promotions'),

    path('test-image/', views.test_image_url, name='test_image'),

    # Аутентификация
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Личный кабинет
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/change-password/', views.change_password_view, name='change_password'),
    path('profile/orders/', views.order_history_view, name='order_history'),
    path('profile/orders/<int:order_id>/', views.order_detail_view, name='order_detail'),

    # Сброс пароля (опционально)
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='store/auth/password_reset.html'
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='store/auth/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='store/auth/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='store/auth/password_reset_complete.html'
         ),
         name='password_reset_complete'),
]