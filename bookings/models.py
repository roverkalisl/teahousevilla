from django.db import models


class BookingInquiry(models.Model):
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
    contacted = models.BooleanField(default=False, help_text="Mark once the owner has followed up with the guest.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Booking Inquiries"

    def __str__(self):
        return f"{self.full_name} — {self.check_in} to {self.check_out}"

    @property
    def nights(self):
        return (self.check_out - self.check_in).days

    @property
    def whatsapp_contact_number(self):
        return self.whatsapp_number or self.phone
