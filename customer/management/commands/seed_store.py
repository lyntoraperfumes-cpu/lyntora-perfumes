from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from customer.models import Category, Product, StoreMessage, StoreSettings

class Command(BaseCommand):
    help = "Create starter Lyntora Perfumes content."

    def handle(self, *args, **options):
        store = StoreSettings.get_solo()
        store.store_name = "Lyntora Perfumes"
        store.tagline = "A signature for every moment."
        store.hero_title = "Discover your signature scent"
        store.hero_subtitle = "Curated fragrances with an elegant, modern shopping experience."
        store.save()

        category_names = ["Floral", "Woody", "Fresh", "Oriental"]
        categories = {}
        for name in category_names:
            c, _ = Category.objects.get_or_create(name=name, defaults={"slug": slugify(name)})
            categories[name] = c

        sample = [
            ("Gloria Eau", "Fresh", Decimal("645.00"), Decimal("795.00"), 4.70),
            ("Bella Rose", "Floral", Decimal("545.00"), Decimal("695.00"), 4.60),
            ("Doux De Liu", "Floral", Decimal("695.00"), Decimal("850.00"), 4.80),
            ("Campo Blu", "Fresh", Decimal("645.00"), Decimal("780.00"), 4.50),
            ("Blanche Parfum", "Woody", Decimal("610.00"), Decimal("750.00"), 4.70),
            ("Sunset Charms", "Oriental", Decimal("540.00"), Decimal("690.00"), 4.60),
            ("Terra Rosso", "Woody", Decimal("720.00"), Decimal("890.00"), 4.90),
            ("Olorious Era", "Oriental", Decimal("610.00"), Decimal("760.00"), 4.50),
        ]
        for name, cat, price, compare, rating in sample:
            Product.objects.get_or_create(
                slug=slugify(name),
                defaults={
                    "name": name, "category": categories[cat], "price": price,
                    "compare_at_price": compare, "rating": rating, "stock": 20,
                    "is_new": True, "is_featured": True, "description": f"Signature {cat.lower()} fragrance from the Lyntora collection."
                }
            )

        StoreMessage.objects.get_or_create(
            title="Welcome to Lyntora Perfumes",
            defaults={"body": "Products, prices and availability are managed live from the store dashboard."}
        )
        self.stdout.write(self.style.SUCCESS("Lyntora starter content created."))
