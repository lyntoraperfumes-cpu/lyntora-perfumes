from django.urls import path
from . import views

app_name = "admin_portal"

urlpatterns = [
    path("", views.admin_login_request, name="admin_login"),
    path("verify/", views.admin_verify, name="admin_verify"),
    path("logout/", views.admin_logout, name="admin_logout"),
    path("dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("products/", views.admin_products, name="admin_products"),
    path("products/new/", views.admin_product_create, name="admin_product_create"),
    path("products/<int:pk>/edit/", views.admin_product_edit, name="admin_product_edit"),
    path("products/<int:pk>/delete/", views.admin_product_delete, name="admin_product_delete"),
    path("categories/", views.admin_categories, name="admin_categories"),
    path("categories/new/", views.admin_category_create, name="admin_category_create"),
    path("messages/", views.admin_messages, name="admin_messages"),
    path("carts/", views.admin_carts, name="admin_carts"),
    path("orders/", views.admin_orders, name="admin_orders"),
    path("orders/<int:pk>/status/", views.admin_order_status, name="admin_order_status"),
    path("hero/", views.admin_hero, name="admin_hero"),
    path("hero/remove/", views.admin_hero_remove, name="admin_hero_remove"),
    path("photos/", views.admin_photo_sections, name="admin_photos"),
    path("photos/new/", views.admin_photo_create, name="admin_photo_create"),
    path("photos/<int:pk>/edit/", views.admin_photo_edit, name="admin_photo_edit"),
    path("photos/<int:pk>/delete/", views.admin_photo_delete, name="admin_photo_delete"),
    path("announcements/", views.admin_announcements, name="admin_announcements"),
    path("settings/", views.admin_settings, name="admin_settings"),
]
