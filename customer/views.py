from decimal import Decimal, InvalidOperation
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.db.models import Q
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    CheckoutForm, CustomerMessageForm, EmailForm, OTPForm
)
from .models import Category, Product, Customer, Cart, CustomerMessage, StoreMessage, SitePhoto, Order
from .utils import (
    active_store_messages, attach_cart_to_customer, cart_total, create_and_send_otp,
    create_order_from_cart, get_or_create_cart, get_store, normalize_email,
    notify_admin, order_whatsapp_url, verify_otp
)


def customer_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        customer_id = request.session.get("customer_id")
        if not customer_id:
            request.session["next_after_login"] = request.get_full_path()
            return redirect("customer:login")
        customer = Customer.objects.filter(pk=customer_id).first()
        if not customer:
            request.session.pop("customer_id", None)
            return redirect("customer:login")
        request.customer = customer
        return view_func(request, *args, **kwargs)
    return wrapper


def _product_queryset():
    return Product.objects.filter(is_active=True).select_related("category")


def home(request):
    products = _product_queryset()
    photos = SitePhoto.objects.filter(active=True)
    context = {
        "new_arrivals": products.filter(is_new=True)[:8],
        "featured": products.filter(is_featured=True)[:4],
        "top_rated": products.order_by("-rating", "-created_at")[:8],
        "categories": Category.objects.filter(active=True),
        "messages": active_store_messages(),
        "hero_photos": photos.filter(placement="hero"),
        "promo_photos": photos.filter(placement="promo"),
        "collection_photos": photos.filter(placement="collection"),
        "news_photos": photos.filter(placement="news"),
        "instagram_photos": photos.filter(placement="instagram"),
    }
    return render(request, "store/home.html", context)


def shop(request):
    qs = _product_queryset()
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    sort = request.GET.get("sort", "recommended")
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
    if category:
        qs = qs.filter(category__slug=category)
    if sort == "price_low":
        qs = qs.order_by("price")
    elif sort == "price_high":
        qs = qs.order_by("-price")
    elif sort == "rating":
        qs = qs.order_by("-rating", "-created_at")
    elif sort == "new":
        qs = qs.order_by("-created_at")
    else:
        qs = qs.order_by("-is_featured", "-rating", "-created_at")
    return render(request, "store/shop.html", {
        "products": qs,
        "categories": Category.objects.filter(active=True),
        "active_category": category,
        "query": q,
        "sort": sort,
    })


def category_products(request, slug):
    get_object_or_404(Category, slug=slug, active=True)
    # Preserve the normal shop filtering while injecting the selected category.
    request.GET = request.GET.copy()
    request.GET["category"] = slug
    return shop(request)


def product_detail(request, slug):
    product = get_object_or_404(_product_queryset(), slug=slug)
    related = _product_queryset().filter(category=product.category).exclude(pk=product.pk)[:4]
    return render(request, "store/product_detail.html", {"product": product, "related": related})


def cart_view(request):
    cart = get_or_create_cart(request)
    items = cart.items.select_related("product", "product__category")
    return render(request, "store/cart.html", {"cart": cart, "items": items, "total": cart_total(cart)})


@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(_product_queryset(), pk=product_id)
    cart = get_or_create_cart(request)
    item, created = cart.items.get_or_create(product=product, defaults={"quantity": 1})
    if not created:
        item.quantity += 1
        item.save(update_fields=["quantity"])
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "count": sum(cart.items.values_list("quantity", flat=True))})
    messages.success(request, f"{product.name} added to your cart.")
    return redirect(request.POST.get("next") or "customer:cart")


@require_POST
def update_cart(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(cart.items.select_related("product"), pk=item_id)
    try:
        quantity = max(1, int(request.POST.get("quantity", 1)))
    except (TypeError, ValueError):
        quantity = 1
    item.quantity = quantity
    item.save(update_fields=["quantity"])
    return redirect("customer:cart")


@require_POST
def remove_from_cart(request, item_id):
    cart = get_or_create_cart(request)
    get_object_or_404(cart.items, pk=item_id).delete()
    return redirect("customer:cart")


def login_request(request):
    if request.session.get("customer_id"):
        return redirect(request.GET.get("next") or "customer:home")
    if request.method == "POST":
        form = EmailForm(request.POST)
        if form.is_valid():
            email = normalize_email(form.cleaned_data["email"])
            create_and_send_otp(email, "login")
            request.session["login_email"] = email
            request.session["login_next"] = request.POST.get("next") or request.GET.get("next") or request.session.get("next_after_login") or "/"
            messages.info(request, "A verification code has been sent to your email.")
            return redirect("customer:verify")
    else:
        form = EmailForm()
    return render(request, "accounts/login.html", {"form": form, "next": request.GET.get("next", "")})


def verify_login(request):
    email = request.session.get("login_email")
    if not email:
        return redirect("customer:login")
    if request.method == "POST":
        form = OTPForm(request.POST)
        if form.is_valid() and verify_otp(email, "login", form.cleaned_data["code"]):
            customer, _ = Customer.objects.get_or_create(email=email)
            customer.is_verified = True
            customer.last_login = timezone.now()
            customer.save(update_fields=["is_verified", "last_login"])
            request.session["customer_id"] = customer.pk
            request.session.pop("login_email", None)
            attach_cart_to_customer(request, customer)
            next_url = request.session.pop("login_next", request.session.pop("next_after_login", "/"))
            return redirect(next_url)
        messages.error(request, "Invalid or expired verification code.")
    else:
        form = OTPForm()
    return render(request, "accounts/verify.html", {"form": form, "email": email})


def logout_view(request):
    request.session.pop("customer_id", None)
    messages.success(request, "You have been signed out.")
    return redirect("customer:home")


@customer_required
def checkout(request):
    cart = get_or_create_cart(request)
    if not cart.items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect("customer:cart")
    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = create_order_from_cart(cart, request.customer, form.cleaned_data)
            store = get_store()
            url = order_whatsapp_url(order, store)
            order.whatsapp_sent = True
            order.save(update_fields=["whatsapp_sent"])
            notify_admin(
                f"New Lyntora order #{order.pk}",
                f"Customer: {order.name}\nEmail: {order.email}\nPhone: {order.phone}\nTotal: ₹{order.total}\nWhatsApp handoff: {url}"
            )
            return redirect("customer:checkout_whatsapp", order_id=order.pk)
    else:
        form = CheckoutForm(initial={"name": request.customer.name, "phone": request.customer.phone})
    return render(request, "store/checkout.html", {
        "form": form,
        "cart": cart,
        "items": cart.items.select_related("product"),
        "total": cart_total(cart),
    })


@customer_required
def checkout_whatsapp(request, order_id):
    order = get_object_or_404(Order, pk=order_id, customer=request.customer)
    url = order_whatsapp_url(order, get_store())
    return render(request, "store/checkout_whatsapp.html", {"order": order, "whatsapp_url": url})


@customer_required
def messages_view(request):
    customer = Customer.objects.filter(pk=request.session.get("customer_id")).first()
    messages_list = CustomerMessage.objects.filter(customer=customer)
    return render(request, "store/messages.html", {"messages_list": messages_list, "contact_page": True})


def send_message(request):
    if request.method != "POST":
        return redirect("customer:home")
    form = CustomerMessageForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Please complete the contact form.")
        return redirect(f"{reverse('customer:home')}#contact")
    customer = Customer.objects.filter(pk=request.session.get("customer_id")).first() if request.session.get("customer_id") else None
    email = form.cleaned_data.get("email") or (customer.email if customer else "")
    if not email:
        messages.error(request, "Email is required for contact messages.")
        return redirect(f"{reverse('customer:home')}#contact")
    if customer is None:
        customer, _ = Customer.objects.get_or_create(email=email, defaults={"name": form.cleaned_data["name"]})
    msg = form.save(commit=False)
    msg.customer = customer
    msg.email = email
    msg.save()
    notify_admin("New customer message", f"Name: {msg.name}\nEmail: {email}\n\n{msg.message}")
    messages.success(request, "Your message has been sent successfully.")
    return redirect(f"{reverse('customer:home')}#contact")


def chatbot(request):
    if request.method != "POST":
        return JsonResponse({"reply": "Ask me about products, prices, categories, cart totals, or delivery help."})
    question = (request.POST.get("message") or "").strip()
    lower = question.lower()
    products = list(_product_queryset()[:100])

    # Malayalam + English intent matching.
    if any(x in lower for x in ["hello", "hi", "hey", "ഹലോ", "നമസ്കാരം", "നമസ്കാരം"]):
        reply = "ഹലോ! 👋 Lyntora Perfumes-ലേക്ക് സ്വാഗതം. Product, price, cart total, category എന്നിവ ചോദിക്കാം."
    elif any(x in lower for x in ["cart", "total", "ആകെ", "കാർട്ട്"]):
        cart = get_or_create_cart(request)
        reply = f"നിങ്ങളുടെ cart total ₹{cart_total(cart):.2f} ആണ്. 🛒"
    elif any(x in lower for x in ["price", "വില", "എത്ര", "rate"]):
        found = [p for p in products if p.name.lower() in lower]
        if found:
            reply = " | ".join(f"{p.name}: ₹{p.price:.2f}" for p in found[:5])
        else:
            reply = "ഏത് perfume-ന്റെ വില വേണം? Product name അയക്കൂ."
    elif any(x in lower for x in ["product", "perfume", "available", "സ്റ്റോക്ക്", "ഉണ്ടോ"]):
        names = ", ".join(p.name for p in products[:8])
        reply = f"ഇപ്പോൾ ലഭ്യമായ ചില products: {names}. കൂടുതൽ കാണാൻ Shop തുറക്കൂ."
    elif any(x in lower for x in ["calculate", "calc", "+", "-", "*", "/", "കണക്ക"]):
        expr = question.replace("₹", "").replace("x", "*").replace("X", "*")
        allowed = set("0123456789.+-*/() ")
        if set(expr) <= allowed:
            try:
                result = eval(expr, {"__builtins__": {}}, {})
                reply = f"കണക്ക്: {result}"
            except Exception:
                reply = "കണക്ക് മനസ്സിലായില്ല. ഉദാ: 500+250*2"
        else:
            reply = "ഉദാ: 500+250*2 എന്ന രീതിയിൽ calculation അയക്കൂ."
    else:
        reply = "ഞാൻ Lyntora Perfumes-ന്റെ store chatbot ആണ്. Product name, price, category, cart total, അല്ലെങ്കിൽ 'ഹെൽപ്' എന്ന് ചോദിക്കൂ."
    return JsonResponse({"reply": reply})
