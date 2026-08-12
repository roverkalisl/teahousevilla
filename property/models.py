import re
from io import BytesIO

from django.core.files.base import ContentFile
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from .utils import to_embed_url

MAX_IMAGE_DIMENSION = 1920


class Property(models.Model):
    """The villa itself. Singleton — only one row is expected to exist."""

    name = models.CharField(max_length=150, default="Teahouse Villa")
    tagline = models.CharField(max_length=200, blank=True)
    short_description = models.TextField(
        blank=True, help_text="Used on the homepage and in search/social previews."
    )
    full_description = models.TextField(blank=True)

    address = models.CharField(max_length=255, blank=True)
    google_maps_url = models.URLField(blank=True, help_text="Link used for the 'Get Directions' button.")
    google_maps_embed_url = models.URLField(blank=True, help_text="Embed src URL for the map iframe.")

    max_guests = models.PositiveIntegerField(default=0)
    bedrooms = models.PositiveIntegerField(default=0)
    bathrooms = models.PositiveIntegerField(default=0)
    property_size_sqm = models.PositiveIntegerField(null=True, blank=True)

    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    house_rules = models.TextField(blank=True)
    cancellation_policy = models.TextField(blank=True)

    phone_number = models.CharField(max_length=30, blank=True)
    whatsapp_number = models.CharField(
        max_length=30, blank=True, help_text="Include country code, digits only, e.g. 94771234567"
    )
    email = models.EmailField(blank=True)

    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    tiktok_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)

    airbnb_url = models.URLField(blank=True, help_text="Link to the Airbnb listing, if any.")
    booking_com_url = models.URLField(blank=True, help_text="Link to the Booking.com listing, if any.")

    hero_image = models.ImageField(upload_to="hero/", blank=True, null=True)
    hero_video_url = models.URLField(
        blank=True, help_text="Optional YouTube/Vimeo URL for an ambient video hero background. If blank, the hero shows an auto-sliding photo gallery instead."
    )
    starting_price_override = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Used on the homepage if no active Price rows are configured.",
    )

    class Meta:
        verbose_name = "Property"
        verbose_name_plural = "Property"

    def __str__(self):
        return self.name

    def get_starting_price(self):
        lowest = self.prices.filter(active=True).order_by("amount").first()
        if lowest:
            return lowest.amount
        return self.starting_price_override

    @property
    def whatsapp_link(self):
        digits = re.sub(r"\D", "", self.whatsapp_number or "")
        return f"https://wa.me/{digits}" if digits else ""

    @property
    def hero_video_embed_url(self):
        return to_embed_url(self.hero_video_url) if self.hero_video_url else ""


class Facility(models.Model):
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Bootstrap Icons class name, e.g. 'bi-wifi'.",
        default="bi-check2-circle",
    )
    description = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name_plural = "Facilities"

    def __str__(self):
        return self.name


class Room(models.Model):
    villa = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="rooms")
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    description = models.TextField(blank=True)
    capacity = models.PositiveIntegerField(default=2, help_text="Maximum guests in this room.")
    bed_type = models.CharField(max_length=100, blank=True)
    bathroom_info = models.CharField(max_length=150, blank=True)
    has_ac = models.BooleanField(default=True)
    size_sqm = models.PositiveIntegerField(null=True, blank=True)
    facilities = models.ManyToManyField(Facility, blank=True, related_name="rooms")
    active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("property:room_detail", args=[self.slug])

    @property
    def cover_image(self):
        cover = self.media.filter(active=True, media_type=Media.IMAGE, is_cover=True).first()
        return cover or self.media.filter(active=True, media_type=Media.IMAGE).first()


class Media(models.Model):
    IMAGE = "image"
    VIDEO = "video"
    MEDIA_TYPE_CHOICES = [(IMAGE, "Image"), (VIDEO, "Video")]

    CATEGORY_CHOICES = [
        ("villa", "Villa"),
        ("bedrooms", "Bedrooms"),
        ("bathrooms", "Bathrooms"),
        ("pool", "Swimming Pool"),
        ("kitchen", "Kitchen"),
        ("garden", "Garden"),
        ("exterior", "Exterior"),
        ("nearby", "Nearby Attractions"),
    ]

    villa = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="media")
    room = models.ForeignKey(
        Room, on_delete=models.CASCADE, related_name="media", null=True, blank=True
    )
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES, default=IMAGE)
    image = models.ImageField(upload_to="gallery/", blank=True, null=True)
    video_url = models.URLField(blank=True, help_text="YouTube or Vimeo URL.")
    caption = models.CharField(max_length=200, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="villa")
    is_cover = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "id"]
        verbose_name_plural = "Media"

    def __str__(self):
        return self.caption or f"{self.get_media_type_display()} #{self.pk}"

    def save(self, *args, **kwargs):
        if self.media_type == self.IMAGE and self.image:
            self._resize_image()
        super().save(*args, **kwargs)

    def _resize_image(self):
        from PIL import Image

        img = Image.open(self.image)
        if img.width <= MAX_IMAGE_DIMENSION and img.height <= MAX_IMAGE_DIMENSION:
            return
        img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.LANCZOS)
        buffer = BytesIO()
        img_format = (img.format or "JPEG")
        if img.mode in ("RGBA", "P") and img_format == "JPEG":
            img = img.convert("RGB")
        img.save(buffer, format=img_format, quality=85, optimize=True)
        self.image.save(self.image.name, ContentFile(buffer.getvalue()), save=False)

    @property
    def video_embed_url(self):
        return to_embed_url(self.video_url)


class Price(models.Model):
    STANDARD = "standard"
    WEEKEND = "weekend"
    PEAK = "peak"
    OFF_SEASON = "off_season"
    SPECIAL_OFFER = "special_offer"
    PRICE_TYPE_CHOICES = [
        (STANDARD, "Standard Rate"),
        (WEEKEND, "Weekend Rate"),
        (PEAK, "Peak Season Rate"),
        (OFF_SEASON, "Off-Season Rate"),
        (SPECIAL_OFFER, "Special Offer"),
    ]

    villa = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="prices")
    price_type = models.CharField(max_length=20, choices=PRICE_TYPE_CHOICES, default=STANDARD)
    start_date = models.DateField(null=True, blank=True, help_text="Leave blank for the standard, always-on rate.")
    end_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.CharField(max_length=200, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["price_type", "start_date"]
        verbose_name_plural = "Prices"

    def __str__(self):
        return f"{self.get_price_type_display()} — {self.amount}"


class Attraction(models.Model):
    BEACH = "beach"
    RESTAURANT = "restaurant"
    LANDMARK = "landmark"
    ACTIVITY = "activity"
    SHOPPING = "shopping"
    OTHER = "other"
    CATEGORY_CHOICES = [
        (BEACH, "Beach"),
        (RESTAURANT, "Restaurant"),
        (LANDMARK, "Landmark"),
        (ACTIVITY, "Activity"),
        (SHOPPING, "Shopping"),
        (OTHER, "Other"),
    ]

    villa = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="attractions")
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=OTHER)
    distance_text = models.CharField(max_length=50, help_text="e.g. '8 km' or '15 min drive'.")
    description = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to="attractions/", blank=True, null=True)
    google_maps_url = models.URLField(blank=True)
    display_order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        return f"{self.name} ({self.distance_text})"


class Testimonial(models.Model):
    GOOGLE = "google"
    AIRBNB = "airbnb"
    BOOKING_COM = "booking_com"
    DIRECT = "direct"
    OTHER = "other"
    SOURCE_CHOICES = [
        (GOOGLE, "Google Reviews"),
        (AIRBNB, "Airbnb"),
        (BOOKING_COM, "Booking.com"),
        (DIRECT, "Direct Guest"),
        (OTHER, "Other"),
    ]
    RATING_CHOICES = [(i, f"{i} Star{'s' if i != 1 else ''}") for i in range(1, 6)]

    villa = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="testimonials")
    guest_name = models.CharField(max_length=100)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=5)
    review_text = models.TextField()
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default=GOOGLE)
    stay_date = models.DateField(null=True, blank=True)
    guest_photo = models.ImageField(upload_to="testimonials/", blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "-id"]

    def __str__(self):
        return f"{self.guest_name} — {self.rating}★"

    @property
    def filled_stars(self):
        return range(self.rating)

    @property
    def empty_stars(self):
        return range(5 - self.rating)
