import django.db.models.deletion
from django.db import migrations, models


def populate_references(apps, schema_editor):
    BookingInquiry = apps.get_model("bookings", "BookingInquiry")
    for booking in BookingInquiry.objects.order_by("created_at", "pk"):
        prefix = booking.created_at.strftime("THV-%Y%m")
        sequence = BookingInquiry.objects.filter(booking_reference__startswith=prefix).count() + 1
        booking.booking_reference = f"{prefix}-{sequence:03d}"
        booking.save(update_fields=["booking_reference"])


class Migration(migrations.Migration):
    dependencies = [("bookings", "0002_availabilityblock_otaavailabilitiesyncstatus")]

    operations = [
        migrations.AddField(
            model_name="bookinginquiry",
            name="booking_reference",
            field=models.CharField(blank=True, max_length=20, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="bookinginquiry",
            name="total_amount",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name="bookinginquiry",
            name="booking_status",
            field=models.CharField(choices=[("PENDING", "Pending"), ("CONFIRMED", "Confirmed"), ("CANCELLED", "Cancelled")], default="PENDING", max_length=12),
        ),
        migrations.AddField(
            model_name="bookinginquiry",
            name="booking_source",
            field=models.CharField(choices=[("WEBSITE", "Website"), ("AIRBNB", "Airbnb"), ("BOOKING_COM", "Booking Com"), ("MANUAL", "Manual")], default="WEBSITE", max_length=12),
        ),
        migrations.AddField(
            model_name="bookinginquiry",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.RunPython(populate_references, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="bookinginquiry",
            name="booking_reference",
            field=models.CharField(blank=True, max_length=20, unique=True),
        ),
        migrations.CreateModel(
            name="BookingNotification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("notification_type", models.CharField(max_length=30)),
                ("channel", models.CharField(default="WHATSAPP", max_length=20)),
                ("recipient", models.CharField(max_length=30)),
                ("message", models.TextField()),
                ("message_status", models.CharField(default="PENDING", max_length=10)),
                ("provider_response", models.TextField(blank=True)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("booking", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="notifications", to="bookings.bookinginquiry")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
