from django import forms

from .models import Customer, CustomerMessage, Product, Category, StoreMessage, StoreSettings, SitePhoto


class EmailForm(forms.Form):
    email = forms.EmailField(label="Email address")


class OTPForm(forms.Form):
    code = forms.CharField(min_length=6, max_length=6, label="Verification code",
                           widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "one-time-code"}))


class CheckoutForm(forms.Form):
    name = forms.CharField(max_length=120)
    phone = forms.CharField(max_length=30, required=False)
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))


class CustomerMessageForm(forms.ModelForm):
    email = forms.EmailField(required=False, label="Email address")
    class Meta:
        model = CustomerMessage
        fields = ["name", "email", "message"]
        widgets = {"message": forms.Textarea(attrs={"rows": 5, "placeholder": "Describe your question or request..."})}


class ProductForm(forms.ModelForm):
    slug = forms.SlugField(required=False, help_text="Leave blank to generate automatically from the product name.")

    class Meta:
        model = Product
        fields = [
            "name", "slug", "category", "description", "price", "compare_at_price",
            "image", "stock", "rating", "is_new", "is_featured", "is_active"
        ]


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "slug", "description", "active"]


class StoreMessageForm(forms.ModelForm):
    class Meta:
        model = StoreMessage
        fields = ["title", "body", "active"]


class StoreSettingsForm(forms.ModelForm):
    class Meta:
        model = StoreSettings
        fields = [
            "store_name", "tagline", "primary_color", "accent_color",
            "gold_color", "support_phone", "whatsapp_number", "support_email",
            "hero_title", "hero_subtitle",
        ]


class SitePhotoForm(forms.ModelForm):
    class Meta:
        model = SitePhoto
        fields = ["title", "placement", "image", "alt_text", "link_url", "active", "sort_order"]


class HeroPhotoForm(forms.ModelForm):
    """Admin-only editor for the main hero image shown on the customer home page."""
    class Meta:
        model = SitePhoto
        fields = ["title", "image", "alt_text", "link_url", "active"]
        labels = {
            "title": "Hero image title",
            "image": "Hero image",
            "alt_text": "Accessibility alt text",
            "link_url": "Optional click URL",
            "active": "Show on customer website",
        }
