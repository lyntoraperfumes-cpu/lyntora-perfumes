from django.urls import path
from . import views

app_name = "customer"

urlpatterns = [
    path("", views.home, name="home"),
    path("shop/", views.shop, name="shop"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),
    path("category/<slug:slug>/", views.category_products, name="category"),
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/update/<int:item_id>/", views.update_cart, name="update_cart"),
    path("cart/remove/<int:item_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("login/", views.login_request, name="login"),
    path("verify/", views.verify_login, name="verify"),
    path("logout/", views.logout_view, name="logout"),
    path("checkout/", views.checkout, name="checkout"),
    path("checkout/whatsapp/<int:order_id>/", views.checkout_whatsapp, name="checkout_whatsapp"),
    path("messages/", views.messages_view, name="messages"),
    path("messages/send/", views.send_message, name="send_message"),
    path("chatbot/", views.chatbot, name="chatbot"),
]
