from .models import Category, StoreSettings

def store_context(request):
    store = StoreSettings.get_solo()
    cart_count = 0
    try:
        cart = request.session.get("cart_preview")
        if cart:
            cart_count = sum(cart.values())
        elif request.session.session_key:
            from .models import Cart
            c = Cart.objects.filter(session_key=request.session.session_key).first()
            if c:
                cart_count = sum(c.items.values_list("quantity", flat=True))
    except Exception:
        pass
    return {
        "store": store,
        "nav_categories": Category.objects.filter(active=True),
        "cart_count": cart_count,
    }
