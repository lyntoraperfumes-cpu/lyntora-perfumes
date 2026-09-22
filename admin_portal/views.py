from functools import wraps
from base64 import b64decode
from binascii import Error as BinasciiError
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from customer.forms import (
    CategoryForm, EmailForm, OTPForm, ProductForm, SitePhotoForm,
    StoreMessageForm, StoreSettingsForm, HeroPhotoForm,
)
from customer.models import (
    Category, Product, Customer, Cart, CustomerMessage, StoreMessage,
    StoreSettings, SitePhoto, Order,
)
from customer.utils import create_and_send_otp, get_store, normalize_email, notify_admin, verify_otp
from PIL import Image


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("is_store_admin"):
            request.session["admin_next"] = request.get_full_path()
            return redirect("admin_portal:admin_login")
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_login_request(request):
    if request.session.get("is_store_admin"):
        return redirect("admin_portal:admin_dashboard")
    if request.method == "POST":
        form = EmailForm(request.POST)
        if form.is_valid():
            email = normalize_email(form.cleaned_data["email"])
            if email != settings.ADMIN_EMAIL:
                messages.error(request, "This email is not authorized for store administration.")
            else:
                create_and_send_otp(email, "admin")
                request.session["admin_login_email"] = email
                messages.info(request, "Admin verification code sent to the authorized email.")
                return redirect("admin_portal:admin_verify")
    else:
        form = EmailForm(initial={"email": settings.ADMIN_EMAIL})
    return render(request, "store_admin/login.html", {"form": form})


def admin_verify(request):
    email = request.session.get("admin_login_email")
    if email != settings.ADMIN_EMAIL:
        return redirect("admin_portal:admin_login")
    if request.method == "POST":
        form = OTPForm(request.POST)
        if form.is_valid() and verify_otp(email, "admin", form.cleaned_data["code"]):
            request.session["is_store_admin"] = True
            request.session["admin_login_email"] = email
            notify_admin("Lyntora admin login", f"Admin login verified for {email}.")
            return redirect("admin_portal:admin_dashboard")
        messages.error(request, "Invalid or expired admin verification code.")
    else:
        form = OTPForm()
    return render(request, "store_admin/verify.html", {"form": form, "email": email})


def admin_logout(request):
    request.session.pop("is_store_admin", None)
    request.session.pop("admin_login_email", None)
    return redirect("admin_portal:admin_login")


@admin_required
def admin_dashboard(request):
    unread = CustomerMessage.objects.filter(is_read=False).count()
    context = {
        "products_count": Product.objects.count(),
        "customers_count": Customer.objects.count(),
        "orders_count": Order.objects.count(),
        "cart_count": Cart.objects.count(),
        "photos_count": SitePhoto.objects.count(),
        "unread_messages": unread,
        "recent_orders": Order.objects.select_related("customer")[:8],
        "recent_messages": CustomerMessage.objects.select_related("customer")[:8],
        "announcements": StoreMessage.objects.filter(active=True)[:5],
    }
    return render(request, "store_admin/dashboard.html", context)


@admin_required
def admin_products(request):
    q = request.GET.get("q", "").strip()
    products = Product.objects.select_related("category")
    if q:
        products = products.filter(Q(name__icontains=q) | Q(category__name__icontains=q))
    return render(request, "store_admin/products.html", {"products": products, "query": q})


def _save_product_form(form):
    product = form.save(commit=False)
    if not product.slug:
        base = slugify(product.name) or "product"
        slug = base
        n = 2
        while Product.objects.filter(slug=slug).exclude(pk=product.pk).exists():
            slug = f"{base}-{n}"
            n += 1
        product.slug = slug
    product.save()
    form.save_m2m()
    return product


def admin_product_create(request):
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        _save_product_form(form)
        messages.success(request, "Product created. It is now available on the customer site.")
        return redirect("admin_portal:admin_products")
    return render(request, "store_admin/form.html", {"form": form, "title": "Add product", "back_url": "admin_portal:admin_products"})


@admin_required
def admin_product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == "POST" and form.is_valid():
        _save_product_form(form)
        messages.success(request, "Product updated. Customer pages use the latest database data immediately.")
        return redirect("admin_portal:admin_products")
    return render(request, "store_admin/form.html", {"form": form, "title": f"Edit: {product.name}", "back_url": "admin_portal:admin_products"})


@admin_required
@require_POST
def admin_product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    messages.success(request, "Product removed.")
    return redirect("admin_portal:admin_products")


@admin_required
def admin_categories(request):
    return render(request, "store_admin/categories.html", {"categories": Category.objects.all()})


@admin_required
def admin_category_create(request):
    form = CategoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Category created.")
        return redirect("admin_portal:admin_categories")
    return render(request, "store_admin/form.html", {"form": form, "title": "Add category", "back_url": "admin_portal:admin_categories"})


@admin_required
def admin_messages(request):
    CustomerMessage.objects.filter(is_read=False).update(is_read=True)
    return render(request, "store_admin/messages.html", {
        "messages_list": CustomerMessage.objects.select_related("customer").all()
    })


@admin_required
def admin_hero(request):
    hero = SitePhoto.objects.filter(placement="hero").order_by("sort_order", "id").first()
    form = HeroPhotoForm(request.POST or None, request.FILES or None, instance=hero)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.placement = "hero"
        obj.sort_order = 0
        obj.save()
        messages.success(request, "Main hero image updated. The customer homepage now uses the new image.")
        return redirect("admin_portal:admin_hero")
    return render(request, "store_admin/hero.html", {"form": form, "hero": hero})


@admin_required
@require_POST
def admin_hero_remove(request):
    SitePhoto.objects.filter(placement="hero").delete()
    messages.success(request, "Main hero image removed. The default Lyntora bottle will be shown on the customer homepage.")
    return redirect("admin_portal:admin_hero")


@admin_required
def admin_photo_sections(request):
    return render(request, "store_admin/photos.html", {"photos": SitePhoto.objects.all()})


@admin_required
def admin_photo_create(request):
    form = SitePhotoForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Website photo added.")
        return redirect("admin_portal:admin_photos")
    return render(request, "store_admin/form.html", {"form": form, "title": "Add website photo", "back_url": "admin_portal:admin_photos"})


@admin_required
def admin_photo_edit(request, pk):
    photo = get_object_or_404(SitePhoto, pk=pk)
    form = SitePhotoForm(request.POST or None, request.FILES or None, instance=photo)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Website photo updated.")
        return redirect("admin_portal:admin_photos")
    return render(request, "store_admin/form.html", {"form": form, "title": f"Edit photo: {photo.title or photo.pk}", "back_url": "admin_portal:admin_photos"})


@admin_required
@require_POST
def admin_photo_delete(request, pk):
    photo = get_object_or_404(SitePhoto, pk=pk)
    photo.delete()
    messages.success(request, "Website photo removed.")
    return redirect("admin_portal:admin_photos")


@admin_required
def admin_carts(request):
    carts = Cart.objects.select_related("customer").prefetch_related("items__product")
    return render(request, "store_admin/carts.html", {"carts": carts})


@admin_required
def admin_orders(request):
    orders = Order.objects.select_related("customer").prefetch_related("items")
    return render(request, "store_admin/orders.html", {"orders": orders})


@admin_required
@require_POST
def admin_order_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    status = request.POST.get("status")
    if status in dict(Order.STATUS_CHOICES):
        order.status = status
        order.save(update_fields=["status"])
    return redirect("admin_portal:admin_orders")


@admin_required
def admin_announcements(request):
    form = StoreMessageForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Admin announcement created.")
        return redirect("admin_portal:admin_announcements")
    return render(request, "store_admin/announcements.html", {
        "form": form,
        "announcements": StoreMessage.objects.all(),
    })


@admin_required
def admin_settings(request):
    obj = get_store()
    form = StoreSettingsForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)

        # The browser crops the logo to the fixed header ratio (3:1) and
        # sends the cropped PNG as a data URL. Saving the cropped file on
        # the server means the customer header always receives the same
        # rectangular logo dimensions without distortion.
        cropped = request.POST.get("logo_cropped", "").strip()
        if cropped:
            try:
                header, encoded = cropped.split(",", 1)
                if not header.startswith("data:image/"):
                    raise ValueError("Invalid image data.")
                raw = b64decode(encoded, validate=True)
                if len(raw) > 8 * 1024 * 1024:
                    raise ValueError("Image is too large.")
                img = Image.open(BytesIO(raw))
                img.verify()
                img = Image.open(BytesIO(raw)).convert("RGBA")
                if img.width < 60 or img.height < 20:
                    raise ValueError("Cropped logo is too small.")
                # Normalize the final stored image to a predictable rectangle.
                img = img.resize((900, 300), Image.Resampling.LANCZOS)
                output = BytesIO()
                img.save(output, format="PNG", optimize=True)
                if obj.logo:
                    obj.logo.delete(save=False)
                obj.logo.save("logo-cropped.png", ContentFile(output.getvalue()), save=False)
            except (ValueError, BinasciiError, OSError):
                messages.error(request, "Could not process the cropped logo. Please choose the image and crop it again.")
                return render(request, "store_admin/settings.html", {
                    "form": form, "title": "Store settings", "back_url": "admin_portal:admin_dashboard"
                })

        obj.save()
        messages.success(request, "Store settings updated. The cropped rectangular logo is now live on the customer website.")
        return redirect("admin_portal:admin_settings")
    return render(request, "store_admin/settings.html", {
        "form": form, "title": "Store settings", "back_url": "admin_portal:admin_dashboard"
    })
