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
    slug = models.SlugField(max_length=200, unique=True)
    brand = models.CharField(max_length=100, blank=True, verbose_name='Бренд')
    description = models.TextField(verbose_name='Описание')
    price = models.DecimalField(max_digits=10, decimal_places=2,
                                validators=[MinValueValidator(0)], verbose_name='Цена')
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