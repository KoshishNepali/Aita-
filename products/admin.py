from django.contrib import admin

from .models import Category, Product


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'base_price', 'is_available', 'created_at')
    list_filter = ('category', 'is_available', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


# Register your models here.
admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
