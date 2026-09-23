# Lyntora Perfumes — Django E-commerce

A maintainable Django perfume-store application inspired by the supplied storefront reference.

## Included

- Passwordless email OTP authentication for customers.
- Passwordless email OTP authentication for the single authorized admin email.
- Admin dashboard for products, categories, orders, carts, customer messages and store settings.
- Unlimited product records with optional images.
- Session cart for guests, automatically attached to a customer after OTP login.
- Checkout/purchase summary opens WhatsApp with product names, individual prices, quantities, totals and customer details.
- Customer ↔ admin interaction/message section.
- Malayalam-friendly store chatbot with product lookup and simple calculations.
- Search, category filtering, sorting, New Arrivals / Top Rated / Related product sections.
- Responsive navigation drawer.
- Theme/logo customization from the admin dashboard.
- DB-backed content: product changes appear on the customer site on the next request without a build step.

## Quick start

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt

copy .env.example .env        # Windows
# cp .env.example .env        # Linux/macOS

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The custom store admin is at `/store-admin/`.

The normal Django admin is at `/django-admin/`.

For local OTP testing, the default email backend prints OTP emails to the terminal.

## Production email

Set the SMTP variables in `.env`. Example:

```text
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-account
EMAIL_HOST_PASSWORD=your-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=no-reply@example.com
```

## Image uploads

Product and logo images are stored under `media/`. In production, configure persistent storage and a proper web server/CDN.

## WhatsApp

The application generates a pre-filled WhatsApp message addressed to:

`8592967239`

No WhatsApp API credential is required for this implementation. The customer's browser opens WhatsApp with the order text already populated.

## Customization

After logging into `/store-admin/`, use **Store Settings** to change:

- store name
- logo
- tagline
- primary / accent / gold colors
- support phone
- support WhatsApp number
- store email

## Security notes

- Change `DJANGO_SECRET_KEY` in production.
- Set `DEBUG=False`.
- Configure `ALLOWED_HOSTS`.
- Use HTTPS.
- Configure a real SMTP provider.
- The OTP is stored hashed, not as plaintext.
- OTPs expire after 10 minutes and are one-time use.
- Rate-limit OTP requests at the reverse-proxy/application level for production.
- Never commit `.env`.

## Project structure

```text
lyntora_perfumes/
├── manage.py
├── requirements.txt
├── .env.example
├── README.md
├── lyntora/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── store/
│   ├── admin.py
│   ├── apps.py
│   ├── context_processors.py
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   ├── utils.py
│   ├── views.py
│   └── migrations/
└── templates/
    ├── base.html
    ├── store/
    ├── accounts/
    └── store_admin/
```

## Website photo management

Use **Store Admin → Website Photos** to add, edit, hide, reorder, or delete images for Hero, Promo, Collection, Latest News, Instagram Feed, and Custom placements. The home page reads these records directly from the database on each request, so changes are reflected immediately.

## Logo placement

Upload the supplied `ac Studio Logo.png` under **Store Admin → Store Settings → Logo**. The recommended placement is the **top-left of the customer header**, aligned with the navigation/search area. The logo field is replaceable later without template changes.

## Customer contact messages

The home page ends with a Contact Us / Talk to Us form. Admin can see customer name, email, message, timestamp, and read status. There is intentionally no admin reply function.

## Application architecture

This build keeps the Lyntora storefront behavior and visual styling while separating the business interfaces into two Django applications inside one project:

- `customer/` — customer-facing store, authentication, cart, checkout, contact/talk-to-us, chatbot.
- `admin_portal/` — passwordless OTP-protected store administration at `/store-admin/`.

Both apps use the same database, so product/category/photo/settings changes made by the admin portal are immediately available to the customer application on the next request.

The customer home page contains the Contact Us / Talk to Us form. The logged-in admin portal never renders that customer form; instead it provides the submitted-message inbox with customer name, email, message and timestamp. There is intentionally no reply control in the admin message view.

Website photos are stored in `SitePhoto` and managed under **Admin → Website Photos** rather than being hard-coded in templates.

### Logo

Upload `ac Studio Logo.png` under **Admin → Store Settings → Logo**. The customer header uses the configured logo in the top-left branding area. The default file name is not hard-coded, so it can be replaced later.

## Two Django applications, one website

The project is intentionally split into two first-party Django apps sharing one database:

1. `customer/` — the public Lyntora Perfumes consumer experience.
2. `admin_portal/` — the private store administration experience at `/store-admin/`.

They are not two separate websites. The root domain serves the customer application, while `/store-admin/` serves the private admin application. Both read/write the same Product, Category, SitePhoto, StoreSettings, Cart, CustomerMessage and Order records. Therefore catalog and visual-content changes are reflected immediately on customer requests without duplicating data.

The admin portal has its own layout and never renders the customer Contact/Talk-to-Us form, customer chatbot, cart header, or public navigation. Instead, submitted customer messages are shown as a read-only inbox containing name, email, message and timestamp.
