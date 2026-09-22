import random
from datetime import timedelta
from urllib.parse import quote

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from .models import Cart, Customer, EmailOTP, Order, OrderItem, Product, StoreMessage, StoreSettings


def normalize_email(email):
    return (email or "").strip().lower()


def generate_otp():
    return f"{random.SystemRandom().randint(0, 999999):06d}"


def create_and_send_otp(email, purpose):
    email = normalize_email(email)
    code = generate_otp()
    now = timezone.now()
    EmailOTP.objects.filter(email=email, purpose=purpose, used=False).update(used=True)
    otp = EmailOTP.objects.create(
        email=email,
        purpose=purpose,
        code_hash=make_password(code),
        expires_at=now + timedelta(minutes=settings.OTP_EXPIRY_MINUTES),
    )
    subject = f"{settings.ADMIN_EMAIL if purpose == 'admin' else 'Lyntora Perfumes'} verification code"
    body = (
        f"Your Lyntora Perfumes verification code is: {code}\n\n"
        f"This code expires in {settings.OTP_EXPIRY_MINUTES} minutes and can be used once.\n"
        f"If you did not request it, you can ignore this email."
    )
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
    return otp


def verify_otp(email, purpose, code):
    email = normalize_email(email)
    otp = EmailOTP.objects.filter(email=email, purpose=purpose, used=False).first()
    if not otp or not otp.is_valid():
        return False
    otp.attempts += 1
    otp.save(update_fields=["attempts"])
    if otp.attempts > 5 or not check_password((code or "").strip(), otp.code_hash):
        return False
    otp.used = True
    otp.save(update_fields=["used"])
    return True


def get_or_create_cart(request):
    if not request.session.session_key:
        request.session.create()
    cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
    customer_id = request.session.get("customer_id")
    if customer_id and cart.customer_id != customer_id:
        cart.customer_id = customer_id
        cart.save(update_fields=["customer"])
    return cart


def attach_cart_to_customer(request, customer):
    cart = get_or_create_cart(request)
    cart.customer = customer
    cart.save(update_fields=["customer"])
    return cart


def cart_total(cart):
    return sum((item.line_total for item in cart.items.select_related("product")), 0)


def create_order_from_cart(cart, customer, data):
    items = list(cart.items.select_related("product"))
    if not items:
        raise ValueError("Your cart is empty.")
    with transaction.atomic():
        order = Order.objects.create(
            customer=customer,
            name=data["name"],
            email=customer.email,
            phone=data.get("phone", ""),
            notes=data.get("notes", ""),
            total=sum((item.line_total for item in items), 0),
        )
        OrderItem.objects.bulk_create([
            OrderItem(
                order=order,
                product_name=item.product.name,
                unit_price=item.product.price,
                quantity=item.quantity,
            )
            for item in items
        ])
    return order


def order_whatsapp_url(order, store):
    lines = [
        f"Hello {store.store_name}, I would like to place an order.",
        "",
        f"Order: #{order.pk}",
        f"Customer: {order.name}",
        f"Email: {order.email}",
        f"Phone: {order.phone or 'Not provided'}",
        "",
        "Products:",
    ]
    for item in order.items.all():
        lines.append(f"- {item.product_name} × {item.quantity} = ₹{item.line_total:.2f}")
    lines += ["", f"Total: ₹{order.total:.2f}"]
    if order.notes:
        lines += ["", f"Notes: {order.notes}"]
    text = quote("\n".join(lines))
    number = "".join(ch for ch in (store.whatsapp_number or settings.WHATSAPP_NUMBER) if ch.isdigit())
    return f"https://wa.me/{number}?text={text}"


def notify_admin(subject, body):
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [settings.ADMIN_EMAIL], fail_silently=True)


def active_store_messages():
    return StoreMessage.objects.filter(active=True)[:5]


def get_store():
    return StoreSettings.get_solo()
