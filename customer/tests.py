from django.test import TestCase
from django.urls import reverse
from .models import Category, Product, Customer, Cart
from .utils import get_or_create_cart

class StoreTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Fresh", slug="fresh")
        self.product = Product.objects.create(
            name="Test Perfume", slug="test-perfume", category=self.category,
            price="500.00", stock=10
        )

    def test_home_loads(self):
        response = self.client.get(reverse("customer:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Lyntora Perfumes")

    def test_guest_can_add_to_cart(self):
        response = self.client.post(reverse("customer:add_to_cart", args=[self.product.id]))
        self.assertEqual(response.status_code, 302)
        cart = Cart.objects.get(session_key=self.client.session.session_key)
        self.assertEqual(cart.items.count(), 1)
