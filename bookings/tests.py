import datetime

from django.test import TestCase

from bookings.models import AvailabilityBlock, BookingInquiry
from property.models import Property


class BookingAvailabilityEngineTests(TestCase):
    def setUp(self):
        self.property = Property.objects.create(name="Test Villa")

    def test_direct_website_booking_makes_dates_unavailable(self):
        BookingInquiry.objects.create(
            full_name="Jane Guest",
            phone="+94 77 123 4567",
            email="jane@example.com",
            check_in=datetime.date(2026, 9, 20),
            check_out=datetime.date(2026, 9, 23),
            adults=2,
        )

        self.assertFalse(
            BookingInquiry.is_date_range_available(
                self.property,
                datetime.date(2026, 9, 20),
                datetime.date(2026, 9, 24),
            )
        )

    def test_airbnb_or_manual_block_makes_dates_unavailable(self):
        AvailabilityBlock.objects.create(
            villa=self.property,
            source=AvailabilityBlock.AIRBNB,
            start_date=datetime.date(2026, 9, 20),
            end_date=datetime.date(2026, 9, 23),
            notes="Airbnb blocked dates",
        )

        self.assertFalse(
            BookingInquiry.is_date_range_available(
                self.property,
                datetime.date(2026, 9, 20),
                datetime.date(2026, 9, 23),
            )
        )

    def test_available_dates_without_conflicts(self):
        self.assertTrue(
            BookingInquiry.is_date_range_available(
                self.property,
                datetime.date(2026, 10, 1),
                datetime.date(2026, 10, 4),
            )
        )
