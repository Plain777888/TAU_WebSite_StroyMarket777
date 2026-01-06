from django.db import models
from django.core.validators import MinValueValidator
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models.signals import post_save

from django.db.models.signals import pre_delete
from django.dispatch import receiver
from supabase import create_client
from django.conf import settings
import os


class Category(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название категории')
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True, verbose_name='Описание')

    image = models.CharField('Изображение (Supabase)', max_length=500, blank=True, null=True)
    image_file = models.ImageField(upload_to='categories/', verbose_name='Изображение',blank=True,  null=True)
    image_url = models.URLField('URL изображения', blank=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('store:category', args=[self.slug])

    def get_image_url(self):
        """Возвращает URL изображения"""
        if self.image:
            from django.conf import settings
            return f"{settings.SUPABASE_URL}/storage/v1/object/public/{self.image}"
        elif self.image_file:
            return self.image_file.url
        elif self.image_url:
            return self.image_url
        return None


class Product(models.Model):
    UNIT_CHOICES = [
        ('шт', 'Штука'),
        ('кг', 'Килограмм'),
        ('л', 'Литр'),
        ('м', 'Метр'),
        ('м²', 'Квадратный метр'),
        ('м³', 'Кубический метр'),
        ('уп', 'Упаковка'),
    ]

    category = models.ForeignKey(Category, related_name='products',
                                 on_delete=models.CASCADE, verbose_name='Категория')
    name = models.CharField(max_length=200, verbose_name='Название товара')
    #slug = models.SlugField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, verbose_name="URL")
    brand = models.CharField(max_length=100, blank=True, verbose_name='Бренд')
    description = models.TextField(verbose_name='Описание')
    price = models.DecimalField(max_digits=10, decimal_places=2,
                                validators=[MinValueValidator(0)], verbose_name='Цена')
    old_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Старая цена",
        help_text="Автоматически заполняется при наличии акции"
    )
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES,
                            default='шт', verbose_name='Единица измерения')
    stock = models.PositiveIntegerField(verbose_name='Количество на складе')
    available = models.BooleanField(default=True, verbose_name='Доступен')
    created = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    image = models.CharField(
        'Основное изображение (Supabase)',
        max_length=500,
        blank=True,
        null=True,
        help_text='Путь к файлу в Supabase Storage, например: products/image.jpg'
    )
    image_file = models.ImageField(upload_to='products/gallery/', verbose_name='Изображение',blank=True,  null=True)

    image_url = models.URLField('URL изображения', blank=True, help_text='Или укажите внешний URL')

    # Характеристики товара
    weight = models.DecimalField(max_digits=10, decimal_places=3, null=True,
                                 blank=True, verbose_name='Вес (кг)')
    dimensions = models.CharField(max_length=100, blank=True, verbose_name='Габариты')
    color = models.CharField(max_length=50, blank=True, verbose_name='Цвет')
    material = models.CharField(max_length=100, blank=True, verbose_name='Материал')

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-created']
        indexes = [
            models.Index(fields=['id', 'slug']),
            models.Index(fields=['name']),
            models.Index(fields=['-created']),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('store:product_detail', args=[self.slug])

    def get_main_image(self):
        """Возвращает основное изображение (приоритет: Supabase > локальное > URL)"""
        if self.image:  # Supabase
            from django.conf import settings
            return f"{settings.SUPABASE_URL}/storage/v1/object/public/products/{self.image}"
        elif self.image_file:  # Локальное
            return self.image_file.url
        elif self.image_url:  # Внешний URL
            return self.image_url
        return None

    @property
    def has_promotion(self):
        """Проверка, есть ли у товара активная акция"""
        try:
            return self.product_promotions.filter(
                promotion__is_active=True,
                promotion__start_date__isnull=False,
                promotion__end_date__isnull=False
            ).filter(
                models.Q(promotion__start_date__lte=timezone.now()) &
                models.Q(promotion__end_date__gte=timezone.now())
            ).exists()
        except:
            return False

    @property
    def current_promotion(self):
        """Получить текущую акцию для товара"""
        try:
            product_promotion = self.product_promotions.filter(
                promotion__is_active=True,
                promotion__start_date__isnull=False,
                promotion__end_date__isnull=False
            ).filter(
                models.Q(promotion__start_date__lte=timezone.now()) &
                models.Q(promotion__end_date__gte=timezone.now())
            ).order_by('-priority').first()

            return product_promotion.promotion if product_promotion else None
        except Exception as e:
            print(f"Error getting current promotion: {e}")
            return None

    @property
    def discount_percentage(self):
        """Получить процент скидки"""
        promotion = self.current_promotion
        if not promotion or not self.price:
            return 0

        try:
            if promotion.discount_type == 'percentage':
                return float(promotion.discount_value)
            elif promotion.discount_type in ['fixed', 'special_price']:
                discount = promotion.calculate_discount(float(self.price))
                if float(self.price) > 0:
                    return round((discount / float(self.price)) * 100, 1)
        except:
            pass
        return 0

    @property
    def discount_amount(self):
        """Получить сумму скидки"""
        promotion = self.current_promotion
        if not promotion or not self.price:
            return 0
        try:
            return promotion.calculate_discount(float(self.price))
        except:
            return 0

    @property
    def sale_price(self):
        """Получить цену со скидкой"""
        if not self.has_promotion:
            return self.price

        promotion = self.current_promotion
        if not promotion:
            return self.price

        try:
            discount = promotion.calculate_discount(float(self.price))
            sale_price = float(self.price) - discount
            return round(max(sale_price, 0), 2)  # Цена не может быть отрицательной
        except:
            return self.price

    @property
    def is_new(self):
        """Проверка, новый ли товар (до 7 дней)"""
        try:
            days_since_creation = (timezone.now() - self.created_at).days
            return days_since_creation <= 7
        except:
            return False

    def save(self, *args, **kwargs):
        """Переопределяем save для автоматической генерации slug и old_price"""
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)

        # Сохраняем старую цену при наличии акции
        if self.has_promotion and not self.old_price:
            self.old_price = self.price

        super().save(*args, **kwargs)

    @property
    def promotion_price(self):
        """Получить цену со скидкой"""
        if not self.has_promotion:
            return self.price

        try:
            promotion = self.current_promotion
            if not promotion:
                return self.price

            discount = promotion.calculate_discount(float(self.price))
            sale_price = float(self.price) - discount
            result = round(max(sale_price, 0), 2)  # Цена не может быть отрицательной

            # Форматируем как Decimal для Django
            from decimal import Decimal
            return Decimal(str(result))
        except Exception as e:
            print(f"Ошибка расчета скидки: {e}")
            return self.price


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images',
                                on_delete=models.CASCADE, verbose_name='Товар')
    image = models.CharField('Изображение (Supabase)', max_length=500, blank=True, null=True)
    image_file = models.ImageField(upload_to='products/gallery/', verbose_name='Изображение',blank=True,  null=True)
    image_url = models.URLField('URL изображения', blank=True)
    alt_text = models.CharField(max_length=200, blank=True, verbose_name='Альтернативный текст')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    #ДАТА ДОБАВЛЕНИЯ ТОВАРА
    #created = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Изображение товара'
        verbose_name_plural = 'Изображения товаров'

    def __str__(self):
        return f"Изображение для {self.product.name}"

    def get_image_url(self):
        """Возвращает URL изображения"""
        if self.image:
            from django.conf import settings
            return f"{settings.SUPABASE_URL}/storage/v1/object/public/products/{self.image}"
        elif self.image_file:
            return self.image_file.url
        elif self.image_url:
            return self.image_url
        return None


class Cart(models.Model):
    session_key = models.CharField(max_length=40, verbose_name='Ключ сессии')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
    created = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
        unique_together = ('session_key', 'product')

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def total_price(self):
        return self.quantity * self.product.price


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'В обработке'),
        ('processing', 'Обрабатывается'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]
    DELIVERY_CHOICES = [
        ('courier', 'Доставка курьером'),
        ('pickup', 'Самовывоз'),
    ]

    PAYMENT_CHOICES = [
        ('cash', 'Наличными при получении'),
        ('card', 'Банковской картой онлайн'),
        ('card_courier', 'Картой курьеру'),
    ]

    # user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    # order_number = models.CharField(max_length=20, unique=True)

    first_name = models.CharField(max_length=50, verbose_name='Имя')
    last_name = models.CharField(max_length=50, verbose_name='Фамилия')
    email = models.EmailField(verbose_name='Email')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    # Доставка
    delivery_type = models.CharField(max_length=20, choices=DELIVERY_CHOICES)
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_address = models.TextField(blank=True, null=True)
    delivery_comment = models.TextField(blank=True, null=True)

    # Самовывоз
    pickup_point = models.CharField(max_length=255, blank=True, null=True)
    pickup_date = models.DateField(blank=True, null=True)
    pickup_time = models.TimeField(blank=True, null=True)

    # Оплата
    payment_type = models.CharField(max_length=20, choices=PAYMENT_CHOICES)

    created = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default='pending', verbose_name='Статус')
    note = models.TextField(blank=True, verbose_name='Примечание')

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created']

    def __str__(self):
        return f"Заказ {self.id}"

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())

    # def save(self, *args, **kwargs):
    #     if not self.order_number:
    #         import random
    #         import string
    #         self.order_number = f"ORD{''.join(random.choices(string.digits, k=8))}"
    #     super().save(*args, **kwargs)

    def get_full_address(self):
        """Возвращает полный адрес для отображения"""
        if self.delivery_type == 'courier' and self.delivery_address:
            return self.delivery_address
        elif self.delivery_type == 'pickup' and self.pickup_point:
            return f"Самовывоз: {self.pickup_point}"
        return "Адрес не указан"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items',
                              on_delete=models.CASCADE, verbose_name='Заказ')
    product = models.ForeignKey(Product, related_name='order_items',
                                on_delete=models.CASCADE, verbose_name='Товар')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')

    class Meta:
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'

    def __str__(self):
        return str(self.id)

    def get_cost(self):
        return self.price * self.quantity


class UserProfile(models.Model):
    """Профиль пользователя"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    address = models.TextField(blank=True, verbose_name='Адрес')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='Аватар')
    email_confirmed = models.BooleanField(default=False, verbose_name='Email подтвержден')

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def __str__(self):
        return f"Профиль {self.user.username}"


from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime


class Promotion(models.Model):
    """Модель акции/распродажи"""
    DISCOUNT_TYPES = [
        ('percentage', 'Процентная скидка'),
        ('fixed', 'Фиксированная сумма'),
        ('buy_one_get_one', '1+1=1'),
        ('special_price', 'Специальная цена'),
    ]

    name = models.CharField(max_length=200, verbose_name="Название акции")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="URL")
    description = models.TextField(verbose_name="Описание акции")
    short_description = models.CharField(max_length=300, blank=True, verbose_name="Краткое описание")
    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPES,
        default='percentage',
        verbose_name="Тип скидки"
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Значение скидки"
    )
    start_date = models.DateTimeField(
        verbose_name="Дата начала",
        null=True,  # Разрешаем null
        blank=True  # Разрешаем пустое поле в форме
    )
    end_date = models.DateTimeField(
        verbose_name="Дата окончания",
        null=True,  # Разрешаем null
        blank=True  # Разрешаем пустое поле в форме
    )
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    image = models.ImageField(upload_to='promotions/', blank=True, null=True, verbose_name="Изображение")
    banner_image = models.ImageField(upload_to='promotions/banners/', blank=True, null=True, verbose_name="Баннер")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Акция"
        verbose_name_plural = "Акции"
        ordering = ['-start_date']

    def __str__(self):
        return self.name

    @property
    def is_current(self):
        """Проверка, действует ли акция сейчас"""
        now = timezone.now()

        # Проверяем, что даты не None
        if self.start_date is None or self.end_date is None:
            return False

        # Проверяем активность
        if not self.is_active:
            return False

        # Проверяем временные рамки
        return self.start_date <= now <= self.end_date

    @property
    def is_upcoming(self):
        """Проверка, будет ли акция в будущем"""
        now = timezone.now()

        if self.start_date is None or self.end_date is None:
            return False

        if not self.is_active:
            return False

        return self.start_date > now

    @property
    def is_expired(self):
        """Проверка, закончилась ли акция"""
        now = timezone.now()

        if self.start_date is None or self.end_date is None:
            return False

        if not self.is_active:
            return False

        return self.end_date < now

    @property
    def days_left(self):
        """Сколько дней осталось до конца акции"""
        if not self.is_current or self.end_date is None:
            return 0

        delta = self.end_date - timezone.now()
        return max(delta.days, 0)

    @property
    def time_left_display(self):
        """Отображение оставшегося времени"""
        if not self.is_current or self.end_date is None:
            return "Не активна"

        delta = self.end_date - timezone.now()
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60

        if days > 0:
            return f"{days} д. {hours} ч."
        elif hours > 0:
            return f"{hours} ч. {minutes} м."
        else:
            return f"{minutes} м."

    def calculate_discount(self, price):
        """Расчет скидки на основе типа акции"""
        if price is None or price <= 0:
            return 0

        price = float(price)
        discount_value = float(self.discount_value)

        if self.discount_type == 'percentage':
            return price * (discount_value / 100)
        elif self.discount_type == 'fixed':
            return min(discount_value, price)
        elif self.discount_type == 'special_price':
            return price - discount_value
        elif self.discount_type == 'buy_one_get_one':
            return price  # Для акции 1+1=1, скидка равна цене одного товара
        return 0

    def save(self, *args, **kwargs):
        """Переопределяем save для автоматической генерации slug"""
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)

        # Устанавливаем дефолтные даты, если они не указаны
        if self.start_date is None:
            self.start_date = timezone.now()

        if self.end_date is None:
            # По умолчанию акция действует 30 дней
            from datetime import timedelta
            if self.start_date:
                self.end_date = self.start_date + timedelta(days=30)
            else:
                self.end_date = timezone.now() + timedelta(days=30)

        super().save(*args, **kwargs)

    @property
    def time_left_display(self):
        """Отображение оставшегося времени (для админки)"""
        if not self.is_current or self.end_date is None:
            return "Не активна"

        delta = self.end_date - timezone.now()
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60

        if days > 0:
            return f"{days} д. {hours} ч."
        elif hours > 0:
            return f"{hours} ч. {minutes} м."
        else:
            return f"{minutes} м."


class ProductPromotion(models.Model):
    """Связь товара с акцией (многие ко многим с дополнительными полями)"""
    product = models.ForeignKey(
        'Product',  # Используем строку для избежания циклического импорта
        on_delete=models.CASCADE,
        related_name='product_promotions',
        verbose_name="Товар"
    )
    promotion = models.ForeignKey(
        Promotion,
        on_delete=models.CASCADE,
        related_name='product_promotions',
        verbose_name="Акция"
    )
    priority = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name="Приоритет",
        help_text="От 1 до 10 (чем выше, тем выше приоритет)"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    class Meta:
        verbose_name = "Товар по акции"
        verbose_name_plural = "Товары по акциям"
        unique_together = ['product', 'promotion']
        ordering = ['-priority', '-created_at']

    def __str__(self):
        return f"{self.product.name} - {self.promotion.name}"

    @property
    def is_active(self):
        """Проверка, активна ли связь товара с акцией"""
        return self.promotion.is_current


# Сигналы для автоматического создания профиля при создании пользователя
# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         UserProfile.objects.create(user=instance)
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    UserProfile.objects.update_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.userprofile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)


@receiver(pre_delete, sender=Product)
def delete_product_images(sender, instance, **kwargs):
    """Удаляет изображения из Supabase при удалении товара"""
    delete_from_supabase(instance.image)

    # Удаляем все изображения галереи
    for product_image in instance.images.all():
        delete_from_supabase(product_image.image)
        # Локальные файлы удалятся автоматически Django


@receiver(pre_delete, sender=ProductImage)
def delete_productimage_images(sender, instance, **kwargs):
    """Удаляет изображение из Supabase при удалении ProductImage"""
    delete_from_supabase(instance.image)


def delete_from_supabase(filepath):
    """Удаляет файл из Supabase"""
    if filepath:
        try:
            supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            supabase.storage.from_('products').remove([filepath])
            print(f"🗑️ Удален файл из Supabase: {filepath}")
        except Exception as e:
            print(f"⚠️ Не удалось удалить файл из Supabase: {e}")


@receiver(pre_delete, sender=Category)
def delete_category_images(sender, instance, **kwargs):
    """Удаляет изображение из Supabase при удалении категории"""
    delete_from_supabase(instance.image)


# from django.db import models
# from django.core.validators import MinValueValidator
# from django.urls import reverse
# from django.contrib.auth.models import User
# from django.db.models.signals import post_save
# from django.dispatch import receiver
#
#
# class Category(models.Model):
#     name = models.CharField(max_length=200, verbose_name='Название категории')
#     slug = models.SlugField(max_length=200, unique=True)
#     description = models.TextField(blank=True, verbose_name='Описание')
#     image = models.ImageField(upload_to='category/', blank=True, verbose_name='Изображение')
#
#     class Meta:
#         verbose_name = 'Категория'
#         verbose_name_plural = 'Категории'
#         ordering = ['name']
#
#     def __str__(self):
#         return self.name
#
#     def get_absolute_url(self):
#         return reverse('store:category', args=[self.slug])
#
#
# class Product(models.Model):
#     UNIT_CHOICES = [
#         ('шт', 'Штука'),
#         ('кг', 'Килограмм'),
#         ('л', 'Литр'),
#         ('м', 'Метр'),
#         ('м²', 'Квадратный метр'),
#         ('м³', 'Кубический метр'),
#         ('уп', 'Упаковка'),
#     ]
#
#     category = models.ForeignKey(Category, related_name='products',
#                                  on_delete=models.CASCADE, verbose_name='Категория')
#     name = models.CharField(max_length=200, verbose_name='Название товара')
#     slug = models.SlugField(max_length=200, unique=True)
#     brand = models.CharField(max_length=100, blank=True, verbose_name='Бренд')
#     description = models.TextField(verbose_name='Описание')
#     price = models.DecimalField(max_digits=10, decimal_places=2,
#                                 validators=[MinValueValidator(0)], verbose_name='Цена')
#     unit = models.CharField(max_length=10, choices=UNIT_CHOICES,
#                             default='шт', verbose_name='Единица измерения')
#     stock = models.PositiveIntegerField(verbose_name='Количество на складе')
#     available = models.BooleanField(default=True, verbose_name='Доступен')
#     created = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
#     updated = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
#     image = models.ImageField(upload_to='products/', blank=True, verbose_name='Основное изображение')
#
#     # Характеристики товара
#     weight = models.DecimalField(max_digits=10, decimal_places=3, null=True,
#                                  blank=True, verbose_name='Вес (кг)')
#     dimensions = models.CharField(max_length=100, blank=True, verbose_name='Габариты')
#     color = models.CharField(max_length=50, blank=True, verbose_name='Цвет')
#     material = models.CharField(max_length=100, blank=True, verbose_name='Материал')
#
#     class Meta:
#         verbose_name = 'Товар'
#         verbose_name_plural = 'Товары'
#         ordering = ['-created']
#         indexes = [
#             models.Index(fields=['id', 'slug']),
#             models.Index(fields=['name']),
#             models.Index(fields=['-created']),
#         ]
#
#     def __str__(self):
#         return self.name
#
#     def get_absolute_url(self):
#         return reverse('store:product_detail', args=[self.slug])
#
#
# from django.db import models
# from django.conf import settings
# import uuid
# import os
#
#
# class Product(models.Model):
#     name = models.CharField(max_length=200)
#     description = models.TextField(blank=True)
#     price = models.DecimalField(max_digits=10, decimal_places=2)
#
#     # ВАЖНО: Используем FileField вместо ImageField
#     image = models.FileField(
#         upload_to='products/',
#         verbose_name='Изображение',
#         null=True,
#         blank=True
#     )
#
#     def __str__(self):
#         return self.name
#
#     def save(self, *args, **kwargs):
#         # Если есть новое изображение
#         if self.image and not self.pk:
#             # Сохраняем сначала без изображения
#             image_file = self.image
#             self.image = None
#             super().save(*args, **kwargs)
#
#             # Теперь загружаем в Supabase
#             self.upload_to_supabase(image_file)
#         else:
#             super().save(*args, **kwargs)
#
#     def upload_to_supabase(self, image_file):
#         """Загружает изображение в Supabase"""
#         from supabase import create_client
#
#         # Генерируем уникальное имя
#         ext = os.path.splitext(image_file.name)[1]
#         filename = f"{uuid.uuid4()}{ext}"
#         filepath = f"products/{filename}"
#
#         # Читаем файл
#         if hasattr(image_file, 'read'):
#             file_content = image_file.read()
#         else:
#             with open(image_file.path, 'rb') as f:
#                 file_content = f.read()
#
#         # Подключаемся к Supabase
#         supabase = create_client(
#             settings.SUPABASE_URL,
#             settings.SUPABASE_KEY
#         )
#
#         try:
#             # Загружаем файл
#             supabase.storage.from_(settings.SUPABASE_BUCKET).upload(
#                 filepath,
#                 file_content,
#                 {"content-type": self.get_content_type(ext)}
#             )
#
#             # Обновляем путь к файлу
#             self.image.name = filepath
#             # Сохраняем только путь (без вызова save, чтобы избежать рекурсии)
#             Product.objects.filter(pk=self.pk).update(image=filepath)
#
#             print(f"✅ Изображение загружено в Supabase: {filepath}")
#
#         except Exception as e:
#             print(f"❌ Ошибка загрузки в Supabase: {e}")
#
#     def get_content_type(self, ext):
#         """Определяет content-type"""
#         ext = ext.lower()
#         if ext in ['.jpg', '.jpeg']:
#             return 'image/jpeg'
#         elif ext == '.png':
#             return 'image/png'
#         elif ext == '.gif':
#             return 'image/gif'
#         elif ext == '.webp':
#             return 'image/webp'
#         return 'application/octet-stream'
#
#     @property
#     def image_url(self):
#         """Возвращает URL изображения из Supabase"""
#         if self.image:
#             return f"{settings.SUPABASE_URL}/storage/v1/object/public/{settings.SUPABASE_BUCKET}/{self.image.name}"
#         return None
#
#
# class Cart(models.Model):
#     session_key = models.CharField(max_length=40, verbose_name='Ключ сессии')
#     product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар')
#     quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
#     created = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
#
#     class Meta:
#         verbose_name = 'Корзина'
#         verbose_name_plural = 'Корзины'
#         unique_together = ('session_key', 'product')
#
#     def __str__(self):
#         return f"{self.quantity} x {self.product.name}"
#
#     @property
#     def total_price(self):
#         return self.quantity * self.product.price
#
#
# class Order(models.Model):
#     STATUS_CHOICES = [
#         ('pending', 'В обработке'),
#         ('processing', 'Обрабатывается'),
#         ('shipped', 'Отправлен'),
#         ('delivered', 'Доставлен'),
#         ('cancelled', 'Отменен'),
#     ]
#
#     first_name = models.CharField(max_length=50, verbose_name='Имя')
#     last_name = models.CharField(max_length=50, verbose_name='Фамилия')
#     email = models.EmailField(verbose_name='Email')
#     phone = models.CharField(max_length=20, verbose_name='Телефон')
#     address = models.TextField(verbose_name='Адрес доставки')
#     created = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
#     updated = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES,
#                               default='pending', verbose_name='Статус')
#     note = models.TextField(blank=True, verbose_name='Примечание')
#
#     class Meta:
#         verbose_name = 'Заказ'
#         verbose_name_plural = 'Заказы'
#         ordering = ['-created']
#
#     def __str__(self):
#         return f"Заказ {self.id}"
#
#     def get_total_cost(self):
#         return sum(item.get_cost() for item in self.items.all())
#
#
# class OrderItem(models.Model):
#     order = models.ForeignKey(Order, related_name='items',
#                               on_delete=models.CASCADE, verbose_name='Заказ')
#     product = models.ForeignKey(Product, related_name='order_items',
#                                 on_delete=models.CASCADE, verbose_name='Товар')
#     price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
#     quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
#
#     class Meta:
#         verbose_name = 'Элемент заказа'
#         verbose_name_plural = 'Элементы заказа'
#
#     def __str__(self):
#         return str(self.id)
#
#     def get_cost(self):
#         return self.price * self.quantity
#
#
# class UserProfile(models.Model):
#     """Профиль пользователя"""
#     user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
#     phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
#     address = models.TextField(blank=True, verbose_name='Адрес')
#     avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='Аватар')
#     email_confirmed = models.BooleanField(default=False, verbose_name='Email подтвержден')
#
#     class Meta:
#         verbose_name = 'Профиль пользователя'
#         verbose_name_plural = 'Профили пользователей'
#
#     def __str__(self):
#         return f"Профиль {self.user.username}"
#
#
# # Сигналы для автоматического создания профиля при создании пользователя
# # @receiver(post_save, sender=User)
# # def create_user_profile(sender, instance, created, **kwargs):
# #     if created:
# #         UserProfile.objects.create(user=instance)
# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     UserProfile.objects.update_or_create(user=instance)
#
# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     try:
#         instance.userprofile.save()
#     except UserProfile.DoesNotExist:
#         UserProfile.objects.create(user=instance)