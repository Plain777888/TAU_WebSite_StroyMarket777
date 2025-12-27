from django.contrib import admin
from .models import Category, Product, ProductImage, Order, OrderItem, Cart

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'available', 'created']
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
    )

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email', 'phone',
                   'status', 'created', 'updated']
    list_filter = ['status', 'created', 'updated']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    inlines = [OrderItemInline]

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['session_key', 'product', 'quantity', 'created']
    list_filter = ['created']
    search_fields = ['session_key', 'product__name']