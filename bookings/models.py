import datetime

from django.db import models
from django.utils import timezone

from property.models import Property


class AvailabilityBlock(models.Model):
    AIRBNB = "airbnb"
    BOOKING_COM = "booking_com"
    DIRECT = "direct"
    MANUAL = "manual"
    SOURCE_CHOICES = [
        (AIRBNB, "Airbnb"),
        (BOOKING_COM, "Booking.com"),
        (DIRECT, "Direct Website"),
        (MANUAL, "Manual Block"),
    ]

    villa = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="availability_blocks")
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default=MANUAL)
    start_date = models.DateField()
    end_date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["start_date", "end_date"]
        verbose_name_plural = "Availability Blocks"

    def __str__(self):
        return f"{self.get_source_display()} — {self.start_date} to {self.end_date}"

    @property
    def nights(self):
        return (self.end_date - self.start_date).days

    def overlaps(self, start_date, end_date):
        if not start_date or not end_date:
            return False
        return start_date < self.end_date and end_date > self.start_date


class OTAAvailabilitySyncStatus(models.Model):
    AIRBNB = "airbnb"
    BOOKING_COM = "booking_com"
    SOURCE_CHOICES = [
        (AIRBNB, "Airbnb"),
        (BOOKING_COM, "Booking.com"),
    ]
    STATUS_NONE = "pending"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_NONE, "Pending"),
        (STATUS_SUCCESS, "Synced"),
        (STATUS_FAILED, "Failed"),
    ]

    villa = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="ota_sync_status")
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NONE)
    last_error = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("villa", "source")]
        verbose_name_plural = "OTA Sync Status"

    def __str__(self):
        return f"{self.get_source_display()} — {self.get_status_display()}"


class BookingInquiry(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_CHOICES = [(value, value.title()) for value in (STATUS_PENDING, STATUS_CONFIRMED, STATUS_CANCELLED)]
    SOURCE_WEBSITE = "WEBSITE"
    SOURCE_AIRBNB = "AIRBNB"
    SOURCE_BOOKING_COM = "BOOKING_COM"
    SOURCE_MANUAL = "MANUAL"
    SOURCE_CHOICES = [(value, value.replace("_", " ").title()) for value in (SOURCE_WEBSITE, SOURCE_AIRBNB, SOURCE_BOOKING_COM, SOURCE_MANUAL)]

    booking_reference = models.CharField(max_length=20, unique=True, blank=True)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30)
    whatsapp_number = models.CharField(max_length=30, blank=True, help_text="Leave blank to use the phone number.")
    email = models.EmailField()

    check_in = models.DateField()
    check_out = models.DateField()
    adults = models.PositiveIntegerField(default=1)
    children = models.PositiveIntegerField(default=0)
    message = models.TextField(blank=True)

    estimated_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    booking_status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDING)
    booking_source = models.CharField(max_length=12, choices=SOURCE_CHOICES, default=SOURCE_WEBSITE)
    contacted = models.BooleanField(default=False, help_text="Mark once the owner has followed up with the guest.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Booking Inquiries"

    def __str__(self):
        return f"{self.booking_reference or 'New booking'} — {self.full_name}"

    @property
    def nights(self):
        return (self.check_out - self.check_in).days

    @property
    def whatsapp_contact_number(self):
        return self.whatsapp_number or self.phone

    @property
    def guest_count(self):
        return self.adults + self.children

    def export_to_connected_channels(self):
        from .services import export_direct_booking_to_connected_channels

        return export_direct_booking_to_connected_channels(self)

    @staticmethod
    def is_date_range_available(property_obj, check_in, check_out):
        if not property_obj or not check_in or not check_out:
            return False
        if check_out <= check_in:
            return False

        direct_conflicts = BookingInquiry.objects.filter(
            booking_status=BookingInquiry.STATUS_CONFIRMED,
            check_in__lt=check_out,
            check_out__gt=check_in,
        )
        if direct_conflicts.exists():
            return False

        if AvailabilityBlock.objects.filter(
            villa=property_obj,
            active=True,
            start_date__lt=check_out,
            end_date__gt=check_in,
        ).exists():
            return False

        return True

    def clean(self):
        super().clean()
        if self.check_in and self.check_out and self.check_out <= self.check_in:
            raise ValueError("Check-out date must be after check-in date.")
        if self.check_in and self.check_in < datetime.date.today():
            raise ValueError("Check-in date can't be in the past.")

    def save(self, *args, **kwargs):
        if self.pk is None:
            property_obj = Property.objects.first()
            if self.booking_status == self.STATUS_CONFIRMED and not BookingInquiry.is_date_range_available(property_obj, self.check_in, self.check_out):
                raise ValueError("Selected dates are unavailable.")
            if not self.booking_reference:
                prefix = timezone.now().strftime("THV-%Y%m")
                sequence = BookingInquiry.objects.filter(booking_reference__startswith=prefix).count() + 1
                self.booking_reference = f"{prefix}-{sequence:03d}"
        super().save(*args, **kwargs)


class BookingNotification(models.Model):
    TYPE_CONFIRMED = "BOOKING_CONFIRMED"
    TYPE_CANCELLED = "BOOKING_CANCELLED"
    CHANNEL_WHATSAPP = "WHATSAPP"
    STATUS_PENDING = "PENDING"
    STATUS_SENT = "SENT"
    STATUS_FAILED = "FAILED"

    booking = models.ForeignKey(BookingInquiry, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=30)
    channel = models.CharField(max_length=20, default=CHANNEL_WHATSAPP)
    recipient = models.CharField(max_length=30)
    message = models.TextField()
    message_status = models.CharField(max_length=10, default=STATUS_PENDING)
    provider_response = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.booking.booking_reference} — {self.notification_type} — {self.message_status}"
