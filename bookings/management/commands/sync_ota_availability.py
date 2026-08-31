import datetime

from django.core.management.base import BaseCommand

from property.models import Property

from bookings.services import refresh_availability_from_ota


class Command(BaseCommand):
    help = "Refresh OTA availability status and sync metadata for the configured property."

    def add_arguments(self, parser):
        parser.add_argument("--property-id", type=int, default=None, help="Optional property id to refresh.")

    def handle(self, *args, **options):
        property_obj = None
        if options["property_id"]:
            property_obj = Property.objects.filter(id=options["property_id"]).first()
        if property_obj is None:
            property_obj = Property.objects.first()

        if not property_obj:
            self.stdout.write(self.style.WARNING("No Property record exists yet; nothing to sync."))
            return

        result = refresh_availability_from_ota(property_obj)
        self.stdout.write(self.style.SUCCESS(f"OTA sync refresh completed for {property_obj.name}: {len(result)} sources processed."))
