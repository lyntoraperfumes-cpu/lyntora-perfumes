from django.contrib import admin
from .models import (
    Category, Product, Customer, EmailOTP, Cart, CartItem,
    CustomerMessage, StoreMessage, StoreSettings, SitePhoto, Order, OrderItem
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "active")
    prepopulated_fields = {"slug": ("name",)}
    list_filter = ("active",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "rating", "is_new", "is_featured", "is_active")
    list_filter = ("category", "is_new", "is_featured", "is_active")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "phone", "is_verified", "last_login")
    search_fields = ("email", "name", "phone")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("session_key", "customer", "updated_at")
    search_fields = ("session_key", "customer__email", "customer__name")


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("cart", "product", "quantity")


@admin.register(CustomerMessage)
class CustomerMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "customer", "is_read", "created_at")
    list_filter = ("is_read",)
    search_fields = ("name", "email", "customer__email", "message")


@admin.register(StoreMessage)
class StoreMessageAdmin(admin.ModelAdmin):
    list_display = ("title", "active", "created_at")
    list_filter = ("active",)


@admin.register(StoreSettings)
class StoreSettingsAdmin(admin.ModelAdmin):
    list_display = ("store_name", "support_email", "updated_at")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "total", "status", "created_at", "whatsapp_sent")
    list_filter = ("status", "whatsapp_sent")
    search_fields = ("name", "email", "phone")


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product_name", "unit_price", "quantity")


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ("email", "purpose", "created_at", "expires_at", "attempts", "used")
    readonly_fields = ("code_hash",)


@admin.register(SitePhoto)
class SitePhotoAdmin(admin.ModelAdmin):
    list_display = ("title", "placement", "active", "sort_order", "updated_at")
    list_filter = ("placement", "active")
    search_fields = ("title", "alt_text")
    ordering = ("placement", "sort_order")
