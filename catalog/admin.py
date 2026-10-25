from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name_fr", "name_ar", "status")
    list_filter = ("status",)
    search_fields = ("name_fr", "name_ar")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("sku", "name_fr", "category", "sale_price", "quantity", "status")
    list_filter = ("status", "category")
    search_fields = ("sku", "barcode", "name_fr", "name_ar", "phone_brand", "phone_model")
    readonly_fields = ("quantity", "created_at", "updated_at")  # le stock ne se modifie que par mouvement
