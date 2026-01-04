# products/admin.py
from django.contrib import admin
from .models import Product
from django.utils.html import format_html


# @admin.register(Product)
# class ProductAdmin(admin.ModelAdmin):
#     list_display = ['name', 'price', 'image_preview', 'created_at']
#     list_filter = ['created_at']
#     search_fields = ['name', 'description']
#     readonly_fields = ['image_preview_large', 'image_url', 'created_at', 'updated_at']
#     fieldsets = (
#         ('Основная информация', {
#             'fields': ('name', 'description', 'price')
#         }),
#         ('Изображение', {
#             'fields': ('image_file', 'image_preview_large', 'image_url')
#         }),
#         ('Даты', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )
#
#     def image_preview(self, obj):
#         if obj.image:
#             return format_html(
#                 '<img src="{}" style="max-height: 50px; max-width: 50px;" />',
#                 obj.image
#             )
#         return "Нет изображения"
#
#     image_preview.short_description = "Изображение"
#
#     def image_preview_large(self, obj):
#         if obj.image:
#             return format_html(
#                 '<img src="{}" style="max-height: 300px; max-width: 100%;" /><br>'
#                 '<small>URL: {}</small>',
#                 obj.image,
#                 obj.image_url or "Локальный файл"
#             )
#         return "Нет изображения"
#
#     image_preview_large.short_description = "Предпросмотр"
#
#     # Отключаем сохранение на экземпляре для оптимизации
#     def save_model(self, request, obj, form, change):
#         # Вызываем стандартный save, который загрузит в Supabase
#         super().save_model(request, obj, form, change)
#
#         # Логируем загрузку
#         if obj.image_url:
#             self.message_user(
#                 request,
#                 f"Изображение загружено в Supabase: {obj.image_url}"
#             )