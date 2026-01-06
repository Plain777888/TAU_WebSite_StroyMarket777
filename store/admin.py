from django.contrib import admin
from .models import Category, Product, ProductImage, Order, OrderItem, Cart
from django.utils.html import format_html
from django import forms
from django.utils.text import slugify
from django.utils.html import format_html
from .models import Product, Category, ProductImage
import os
import uuid
from supabase import create_client
from django.conf import settings

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'alt_text', 'order', 'image_preview']
    list_filter = ['product']
    ordering = ['product', 'order']

    def image_preview(self, obj):
        image_url = obj.get_image_url()
        if image_url:
            return format_html(
                '<img src="{}" style="max-height: 50px;" />',
                image_url
            )
        return "📷"

    image_preview.short_description = "Превью"



class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'short_description': forms.Textarea(attrs={'rows': 2, 'cols': 80}),
            'description': forms.Textarea(attrs={'rows': 6, 'cols': 80}),
            'slug': forms.TextInput(attrs={'placeholder': 'Автозаполнение из названия'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Значения по умолчанию для нового товара
        if not self.instance.pk:
            self.initial.setdefault('unit', 'шт')
            self.initial.setdefault('stock', 0)
            self.initial.setdefault('available', True)

        # Помечаем обязательные поля
        for field_name, field in self.fields.items():
            if field.required:
                field.widget.attrs['class'] = 'required'
                field.label = f"{field.label} *"

    def clean(self):
        cleaned_data = super().clean()

        # Автозаполнение slug
        if not cleaned_data.get('slug') and cleaned_data.get('name'):
            cleaned_data['slug'] = slugify(cleaned_data['name'])

        # Автогенерация SKU если пустой
        if not cleaned_data.get('sku'):
            cleaned_data['sku'] = f"SKU-{uuid.uuid4().hex[:8].upper()}"

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Обработка изображений
        self.handle_images(instance)

        if commit:
            instance.save()
            self.save_m2m()

        return instance

    def handle_images(self, instance):
        """Обрабатывает загрузку изображений"""

        # 1. Основное изображение в Supabase
        if 'image' in self.files and self.files['image']:
            self.upload_to_supabase(instance, 'image')

        # 2. Локальное изображение
        elif 'image_file' in self.files and self.files['image_file']:
            # Django сам сохранит в MEDIA_ROOT
            pass

        # 3. Если загружено локальное изображение, можно автоматически загрузить в Supabase
        # if ('image_file' in self.changed_data or 'image' in self.changed_data) and instance.image_file:
            # Автоматическая загрузка локального изображения в Supabase
            try:
                self.upload_local_to_supabase(instance)
            except Exception as e:
                print(f"⚠️ Не удалось загрузить локальное изображение в Supabase: {e}")

        # 4. Если изображение удалено (очищено поле)
        if 'image' in self.changed_data and not self.cleaned_data.get('image'):
            # Можно удалить старый файл из Supabase
            self.delete_old_supabase_image(instance, 'image')

    def delete_old_supabase_image(self, instance, field_name):
        """Удаляет старый файл из Supabase"""
        old_value = instance.__dict__.get(field_name)
        if old_value:
            try:
                supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                supabase.storage.from_('products').remove([old_value])
                print(f"🗑️ Удален старый файл из Supabase: {old_value}")
            except Exception as e:
                print(f"⚠️ Не удалось удалить файл из Supabase: {e}")

    def upload_to_supabase(self, instance, field_name):
        """Загружает файл в Supabase"""
        image_file = self.files[field_name]

        # Генерируем уникальное имя
        ext = os.path.splitext(image_file.name)[1].lower()
        filename = f"product_{uuid.uuid4().hex[:8]}{ext}"
        filepath = f"products/{filename}"

        # Определяем content-type
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
        }
        content_type = content_types.get(ext, 'image/jpeg')

        # Загружаем
        try:
            supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            file_content = image_file.read()

            supabase.storage.from_('products').upload(
                filepath,
                file_content,
                {"content-type": content_type}
            )

            # Сохраняем путь
            setattr(instance, field_name, filepath)
            print(f"✅ Изображение загружено в Supabase: {filepath}")

        except Exception as e:
            print(f"❌ Ошибка загрузки в Supabase: {e}")

    def upload_local_to_supabase(self, instance):
        """Загружает локальное изображение в Supabase"""
        if not instance.image_file:
            return

        # ВАЖНО: Файл может быть еще не сохранен на диск!

        # Способ 1: Чтение из памяти (если файл еще не сохранен)
        if hasattr(instance.image_file, 'file'):
            # Файл в памяти
            file_content = instance.image_file.read()
            instance.image_file.seek(0)  # Возвращаем позицию чтения
        else:
            # Файл уже сохранен на диск
            try:
                with open(instance.image_file.path, 'rb') as f:
                    file_content = f.read()
            except (ValueError, OSError):
                # Файл не существует на диске
                print("⚠️ Файл еще не сохранен на диск")
                return

        # Генерируем имя
        ext = os.path.splitext(instance.image_file.name)[1].lower()
        filename = f"product_{uuid.uuid4().hex[:8]}{ext}"
        filepath = f"products/{filename}"

        # Загружаем
        try:
            supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            supabase.storage.from_('products').upload(
                filepath,
                file_content,
                {"content-type": f"image/{ext[1:]}" if ext else 'image/jpeg'}
            )

            # Обновляем поле
            instance.image = filepath
            print(f"✅ Локальное изображение загружено в Supabase: {filepath}")

        except Exception as e:
            print(f"❌ Ошибка загрузки в Supabase: {e}")




class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = '__all__'

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Автоматическая загрузка в Supabase если выбрано локальное изображение
        if 'image_file' in self.files and self.files['image_file']:
            # Если загружено локальное изображение, автоматически загружаем в Supabase
            try:
                self.upload_local_to_supabase(instance)
            except Exception as e:
                print(f"⚠️ ProductImage: Не удалось загрузить в Supabase: {e}")

        # Загрузка в Supabase если напрямую выбрано поле image
        elif 'image' in self.files and self.files['image']:
            self.upload_to_supabase(instance, 'image')

        if commit:
            instance.save()

        return instance

    def upload_to_supabase(self, instance, field_name):
        """Загружает файл в Supabase (аналогично ProductForm)"""
        image_file = self.files[field_name]

        # Генерируем уникальное имя
        ext = os.path.splitext(image_file.name)[1].lower()
        filename = f"product_gallery_{uuid.uuid4().hex[:8]}{ext}"
        filepath = f"products/gallery/{filename}"  # Другая папка для галереи

        # Определяем content-type
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
        }
        content_type = content_types.get(ext, 'image/jpeg')

        # Загружаем
        try:
            supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            file_content = image_file.read()

            supabase.storage.from_('products').upload(
                filepath,
                file_content,
                {"content-type": content_type}
            )

            # Сохраняем путь
            setattr(instance, field_name, filepath)
            print(f"✅ ProductImage: Изображение загружено в Supabase: {filepath}")

        except Exception as e:
            print(f"❌ ProductImage: Ошибка загрузки в Supabase: {e}")
            # Можно показать ошибку пользователю
            raise forms.ValidationError(f"Ошибка загрузки изображения: {e}")

    def upload_local_to_supabase(self, instance):
        """Загружает локальное изображение в Supabase"""
        if not instance.image_file:
            return

        # Читаем локальный файл
        file_path = instance.image_file.path if hasattr(instance.image_file, 'path') else None

        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                file_content = f.read()
        else:
            # Если файл в памяти
            file_content = instance.image_file.read()
            instance.image_file.seek(0)  # Возвращаем позицию

        # Генерируем имя
        ext = os.path.splitext(instance.image_file.name)[1].lower()
        filename = f"product_gallery_{uuid.uuid4().hex[:8]}{ext}"
        filepath = f"products/gallery/{filename}"

        # Загружаем
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        supabase.storage.from_('products').upload(
            filepath,
            file_content,
            {"content-type": f"image/{ext[1:]}" if ext else 'image/jpeg'}
        )

        # Обновляем поле
        instance.image = filepath
        print(f"✅ ProductImage: Локальное изображение загружено в Supabase: {filepath}")

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    form = ProductImageForm
    extra = 1
    fields = ['image_file', 'image', 'image_url', 'alt_text', 'order']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.pk:  # Если объект уже сохранен
            image_url = obj.get_image_url()
            if image_url:
                return format_html(
                    '<img src="{}" style="max-height: 100px;" />',
                    image_url
                )
        return "Загрузите изображение"

    image_preview.short_description = "Превью"

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductForm
    list_display = ['name', 'category', 'price', 'stock', 'available','image_preview', 'created']
    list_filter = ['available', 'created', 'category']
    list_editable = ['price', 'stock', 'available']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    inlines = [ProductImageInline]
    fieldsets = (
        ('Основная информация', {
            'fields': ('category', 'name', 'slug', 'description', 'image')
        }),
        ('Цена и наличие', {
            'fields': ('price', 'unit', 'stock', 'available')
        }),
        ('Характеристики', {
            'fields': ('brand', 'weight', 'dimensions', 'color', 'material'),
            'classes': ('collapse',)
        }),
        ('Изображения (выберите один вариант)', {
            'fields': (
                ('image_display',
                'image_file', 'image_url'),
            ),
            'description': '''
                        <strong>Загрузите изображение одним из способов:</strong><br>
                        1. В Supabase Storage (рекомендуется) - поле "image"<br>
                        2. Локально на сервер - поле "image_file"<br>
                        3. По URL - поле "image_url"
                    '''
        }),
    )

    readonly_fields = ['image_display']

    def image_preview(self, obj):
        """Превью в списке"""
        image_url = obj.get_main_image()
        if image_url:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px;" />',
                image_url
            )
        return "📷"

    image_preview.short_description = "Изобр."

    def image_display(self, obj):
        """Большое превью в форме редактирования"""
        image_url = obj.get_main_image()
        if image_url:
            return format_html(
                '''
                <div style="margin: 10px 0;">
                    <a href="{}" target="_blank">
                        <img src="{}" style="max-height: 200px; max-width: 200px; 
                              border: 1px solid #ddd; border-radius: 4px;" />
                    </a>
                    <div style="margin-top: 5px; color: #666; font-size: 12px;">
                        <a href="{}" target="_blank">Открыть в новом окне</a>
                    </div>
                </div>
                ''',
                image_url, image_url, image_url
            )
        return "❌ Изображение не загружено"

    image_display.short_description = "Текущее изображение"
    image_display.allow_tags = True



class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email', 'phone',
                   'status', 'created', 'updated','delivery_address','delivery_type']
    list_filter = ['status', 'created', 'updated']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    inlines = [OrderItemInline]

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['session_key', 'product', 'quantity', 'created']
    list_filter = ['created']
    search_fields = ['session_key', 'product__name']


from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Category, Product, Promotion, ProductPromotion, ProductImage
from .forms import PromotionForm

class ProductPromotionInline(admin.TabularInline):
    """Inline для акций товара"""
    model = ProductPromotion
    extra = 1
    autocomplete_fields = ['product']


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ['name', 'discount_type', 'discount_value', 'start_date', 'end_date', 'is_active']
    list_filter = ['is_active', 'discount_type']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}

    # УБРАТЬ time_left_display отсюда ↓
    readonly_fields = ['created_at', 'updated_at']  # Было: ['created_at', 'updated_at', 'time_left_display']

    inlines = [ProductPromotionInline]

    fieldsets = [
        ('Основная информация', {
            'fields': ['name', 'slug', 'description', 'short_description', 'is_active']
        }),
        ('Параметры скидки', {
            'fields': ['discount_type', 'discount_value']
        }),
        ('Сроки действия', {
            'fields': ['start_date', 'end_date']  # Было: ['start_date', 'end_date', 'time_left_display']
        }),
        ('Изображения', {
            'fields': ['image', 'banner_image']
        }),
    ]

    # Метод можно оставить, но убрать из полей
    def time_left_display(self, obj):
        """Отображение оставшегося времени"""
        if obj.start_date and obj.end_date:
            return f"{obj.name} - расчет времени"
        return "Даты не установлены"

    time_left_display.short_description = 'Осталось времени'


@admin.register(ProductPromotion)
class ProductPromotionAdmin(admin.ModelAdmin):
    list_display = ['product', 'promotion', 'priority', 'discount_info']
    list_filter = ['promotion']
    search_fields = ['product__name', 'promotion__name']
    autocomplete_fields = ['product', 'promotion']

    def discount_info(self, obj):
        if obj.promotion and obj.product:
            discount = obj.promotion.calculate_discount(float(obj.product.price))
            return f"-{discount:.2f} ₽ ({obj.product.discount_percentage}%)"
        return "—"

    discount_info.short_description = 'Скидка'



# from django.contrib import admin
# from .models import Category, Product, ProductImage, Order, OrderItem, Cart
#
# @admin.register(Category)
# class CategoryAdmin(admin.ModelAdmin):
#     list_display = ['name', 'slug']
#     prepopulated_fields = {'slug': ('name',)}
#     search_fields = ['name']
#
# class ProductImageInline(admin.TabularInline):
#     model = ProductImage
#     extra = 1
#
#
# from django.contrib import admin
# from django.utils.html import format_html
# from .models import Product
#
#
# class ProductAdmin(admin.ModelAdmin):
#     list_display = ['name', 'price', 'image_preview']
#     readonly_fields = ['image_preview']
#
#     fieldsets = (
#         ('Основная информация', {
#             'fields': ('name', 'description', 'price')
#         }),
#         ('Изображение', {
#             'fields': ('image', 'image_preview')
#         }),
#     )
#
#     def image_preview(self, obj):
#         if obj.image_url:
#             return format_html(
#                 '<img src="{}" style="max-height: 200px; max-width: 200px;" />',
#                 obj.image_url
#             )
#         return "Нет изображения"
#
#     image_preview.short_description = "Превью"
#
#
# # admin.site.register(Product, ProductAdmin)
# #
# # @admin.register(Product)
# # class ProductAdmin(admin.ModelAdmin):
# #     list_display = ['name', 'category', 'price', 'stock', 'available', 'created']
# #     list_filter = ['available', 'created', 'category']
# #     list_editable = ['price', 'stock', 'available']
# #     prepopulated_fields = {'slug': ('name',)}
# #     search_fields = ['name', 'description']
# #     inlines = [ProductImageInline]
# #     fieldsets = (
# #         ('Основная информация', {
# #             'fields': ('category', 'name', 'slug', 'description', 'image')
# #         }),
# #         ('Цена и наличие', {
# #             'fields': ('price', 'unit', 'stock', 'available')
# #         }),
# #         ('Характеристики', {
# #             'fields': ('brand', 'weight', 'dimensions', 'color', 'material'),
# #             'classes': ('collapse',)
# #         }),
# #     )
#
# class OrderItemInline(admin.TabularInline):
#     model = OrderItem
#     raw_id_fields = ['product']
#
# @admin.register(Order)
# class OrderAdmin(admin.ModelAdmin):
#     list_display = ['id', 'first_name', 'last_name', 'email', 'phone',
#                    'status', 'created', 'updated']
#     list_filter = ['status', 'created', 'updated']
#     search_fields = ['first_name', 'last_name', 'email', 'phone']
#     inlines = [OrderItemInline]
#
# @admin.register(Cart)
# class CartAdmin(admin.ModelAdmin):
#     list_display = ['session_key', 'product', 'quantity', 'created']
#     list_filter = ['created']
#     search_fields = ['session_key', 'product__name']

# store/admin.py - ПОЛН# store/admin.py - ПОЛНЫЙ РАБОЧИЙ ВАРИАНТ
# from django.contrib import admin
# from django import forms
# from django.utils.text import slugify
# from .models import Product, Category
# import os
# import uuid
# from supabase import create_client
# from django.conf import settings
#
# class ProductForm(forms.ModelForm):
#     class Meta:
#         model = Product
#         fields = '__all__'
#         widgets = {
#             'description': forms.Textarea(attrs={'rows': 4}),
#             'slug': forms.TextInput(attrs={'placeholder': 'auto-generated'}),
#         }
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#
#         # Устанавливаем значения по умолчанию для нового продукта
#         if not self.instance.pk:
#             self.initial.setdefault('unit', 'шт')
#             self.initial.setdefault('stock', 0)
#             self.initial.setdefault('available', True)
#
#     def clean_slug(self):
#         """Автоматически генерируем slug из названия"""
#         slug = self.cleaned_data.get('slug')
#         name = self.cleaned_data.get('name')
#
#         if not slug and name:
#             slug = slugify(name)
#
#         # Делаем уникальным
#         original_slug = slug
#         counter = 1
#
#         while Product.objects.filter(slug=slug).exclude(pk=self.instance.pk).exists():
#             slug = f'{original_slug}-{counter}'
#             counter += 1
#
#         return slug
#
#     def save(self, commit=True):
#         instance = super().save(commit=False)
#
#         # Загрузка изображения в Supabase
#         if 'image' in self.files:
#             self.upload_to_supabase(instance)
#
#         if commit:
#             instance.save()
#
#         return instance
#
#     def upload_to_supabase(self, instance):
#         """Загружает изображение в Supabase Storage"""
#         image_file = self.files['image']
#
#         # Генерируем уникальное имя файла
#         original_name = image_file.name
#         ext = os.path.splitext(original_name)[1].lower()
#         filename = f"{uuid.uuid4().hex[:8]}{ext}"
#         filepath = f"products/{filename}"
#
#         # Загружаем в Supabase
#         supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
#         file_content = image_file.read()
#
#         try:
#             # Определяем content-type
#             if ext in ['.jpg', '.jpeg']:
#                 content_type = 'image/jpeg'
#             elif ext == '.png':
#                 content_type = 'image/png'
#             elif ext == '.gif':
#                 content_type = 'image/gif'
#             elif ext == '.webp':
#                 content_type = 'image/webp'
#             else:
#                 content_type = 'image/jpeg'  # По умолчанию
#
#             # Загружаем файл
#             response = supabase.storage.from_('products').upload(
#                 filepath,
#                 file_content,
#                 {"content-type": content_type}
#             )
#
#             # Сохраняем путь к файлу
#             instance.image = filepath
#             print(f"✅ Изображение загружено в Supabase: {filepath}")
#
#         except Exception as e:
#             print(f"❌ Ошибка загрузки в Supabase: {e}")
#             # Можно показать сообщение пользователю
#             from django.contrib import messages
#             # messages.error(self.request, f"Ошибка загрузки изображения: {e}")
#
# @admin.register(Product)
# class ProductAdmin(admin.ModelAdmin):
#     form = ProductForm
#     list_display = ['name', 'category', 'price', 'stock', 'available', 'image_preview']
#     list_filter = ['category', 'available', 'created']
#     search_fields = ['name', 'description', 'brand']
#     prepopulated_fields = {'slug': ('name',)}
#     readonly_fields = ['image_preview', 'created', 'updated']
#
#     fieldsets = (
#         ('Основная информация', {
#             'fields': ('category', 'name', 'slug', 'brand', 'description')
#         }),
#         ('Цена и наличие', {
#             'fields': ('price', 'unit', 'stock', 'available')
#         }),
#         ('Изображение', {
#             'fields': ('image', 'image_preview')
#         }),
#         ('Дополнительная информация', {
#             'fields': ('weight', 'dimensions', 'color', 'material'),
#             'classes': ('collapse',)
#         }),
#         ('Мета-данные', {
#             'fields': ('created', 'updated'),
#             'classes': ('collapse',)
#         }),
#     )
#
#     def image_preview(self, obj):
#         if obj.image:
#             url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{obj.image}"
#             return f'''
#             <div style="margin-bottom: 10px;">
#                 <a href="{url}" target="_blank" style="display: inline-block;">
#                     <img src="{url}" style="max-height: 150px; max-width: 150px; border: 1px solid #ddd; border-radius: 4px;" />
#                 </a>
#                 <div style="margin-top: 5px; font-size: 12px; color: #666;">
#                     <a href="{url}" target="_blank">{obj.image}</a>
#                 </div>
#             </div>
#             '''
#         return "❌ Нет изображения"
#
#     image_preview.short_description = "Превью"
#     image_preview.allow_tags = True
#
# # Если есть модель Category, зарегистрируем её тоже
# @admin.register(Category)
# class CategoryAdmin(admin.ModelAdmin):
#     list_display = ['name', 'slug']
#     prepopulated_fields = {'slug': ('name',)}ЫЙ РАБОЧИЙ ВАРИАНТ

# from django.contrib import admin
# from django import forms
# from django.utils.text import slugify
# from .models import Product, Category
# import os
# import uuid
# from supabase import create_client
# from django.conf import settings
#
# class ProductForm(forms.ModelForm):
#     class Meta:
#         model = Product
#         fields = '__all__'
#         widgets = {
#             'description': forms.Textarea(attrs={'rows': 4}),
#             'slug': forms.TextInput(attrs={'placeholder': 'auto-generated'}),
#         }
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#
#         # Устанавливаем значения по умолчанию для нового продукта
#         if not self.instance.pk:
#             self.initial.setdefault('unit', 'шт')
#             self.initial.setdefault('stock', 0)
#             self.initial.setdefault('available', True)
#
#     def clean_slug(self):
#         """Автоматически генерируем slug из названия"""
#         slug = self.cleaned_data.get('slug')
#         name = self.cleaned_data.get('name')
#
#         if not slug and name:
#             slug = slugify(name)
#
#         # Делаем уникальным
#         original_slug = slug
#         counter = 1
#
#         while Product.objects.filter(slug=slug).exclude(pk=self.instance.pk).exists():
#             slug = f'{original_slug}-{counter}'
#             counter += 1
#
#         return slug
#
#     def save(self, commit=True):
#         instance = super().save(commit=False)
#
#         # Загрузка изображения в Supabase
#         if 'image' in self.files:
#             self.upload_to_supabase(instance)
#
#         if commit:
#             instance.save()
#
#         return instance
#
#     def upload_to_supabase(self, instance):
#         """Загружает изображение в Supabase Storage"""
#         image_file = self.files['image']
#
#         # Генерируем уникальное имя файла
#         original_name = image_file.name
#         ext = os.path.splitext(original_name)[1].lower()
#         filename = f"{uuid.uuid4().hex[:8]}{ext}"
#         filepath = f"products/{filename}"
#
#         # Загружаем в Supabase
#         supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
#         file_content = image_file.read()
#
#         try:
#             # Определяем content-type
#             if ext in ['.jpg', '.jpeg']:
#                 content_type = 'image/jpeg'
#             elif ext == '.png':
#                 content_type = 'image/png'
#             elif ext == '.gif':
#                 content_type = 'image/gif'
#             elif ext == '.webp':
#                 content_type = 'image/webp'
#             else:
#                 content_type = 'image/jpeg'  # По умолчанию
#
#             # Загружаем файл
#             response = supabase.storage.from_('products').upload(
#                 filepath,
#                 file_content,
#                 {"content-type": content_type}
#             )
#
#             # Сохраняем путь к файлу
#             instance.image = filepath
#             print(f"✅ Изображение загружено в Supabase: {filepath}")
#
#         except Exception as e:
#             print(f"❌ Ошибка загрузки в Supabase: {e}")
#             # Можно показать сообщение пользователю
#             from django.contrib import messages
#             # messages.error(self.request, f"Ошибка загрузки изображения: {e}")
#
# @admin.register(Product)
# class ProductAdmin(admin.ModelAdmin):
#     form = ProductForm
#     list_display = ['name', 'category', 'price', 'stock', 'available', 'image_preview']
#     list_filter = ['category', 'available', 'created']
#     search_fields = ['name', 'description', 'brand']
#     prepopulated_fields = {'slug': ('name',)}
#     readonly_fields = ['image_preview', 'created', 'updated']
#
#     fieldsets = (
#         ('Основная информация', {
#             'fields': ('category', 'name', 'slug', 'brand', 'description')
#         }),
#         ('Цена и наличие', {
#             'fields': ('price', 'unit', 'stock', 'available')
#         }),
#         ('Изображение', {
#             'fields': ('image', 'image_preview')
#         }),
#         ('Дополнительная информация', {
#             'fields': ('weight', 'dimensions', 'color', 'material'),
#             'classes': ('collapse',)
#         }),
#         ('Мета-данные', {
#             'fields': ('created', 'updated'),
#             'classes': ('collapse',)
#         }),
#     )
#
#     def image_preview(self, obj):
#         if obj.image:
#             url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{obj.image}"
#             return f'''
#             <div style="margin-bottom: 10px;">
#                 <a href="{url}" target="_blank" style="display: inline-block;">
#                     <img src="{url}" style="max-height: 150px; max-width: 150px; border: 1px solid #ddd; border-radius: 4px;" />
#                 </a>
#                 <div style="margin-top: 5px; font-size: 12px; color: #666;">
#                     <a href="{url}" target="_blank">{obj.image}</a>
#                 </div>
#             </div>
#             '''
#         return "❌ Нет изображения"
#
#     image_preview.short_description = "Превью"
#     image_preview.allow_tags = True
#
# # Если есть модель Category, зарегистрируем её тоже
# @admin.register(Category)
# class CategoryAdmin(admin.ModelAdmin):
#     list_display = ['name', 'slug']
#     prepopulated_fields = {'slug': ('name',)}
#
# @admin.register(Order)
# class OrderAdmin(admin.ModelAdmin):
#     list_display = ['id', 'first_name', 'last_name', 'email', 'phone',
#                    'status', 'created', 'updated']
#     list_filter = ['status', 'created', 'updated']
#     search_fields = ['first_name', 'last_name', 'email', 'phone']
#     inlines = [OrderItemInline]
#
# @admin.register(Cart)
# class CartAdmin(admin.ModelAdmin):
#     list_display = ['session_key', 'product', 'quantity', 'created']
#     list_filter = ['created']
#     search_fields = ['session_key', 'product__name']