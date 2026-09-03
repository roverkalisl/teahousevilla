import datetime

from django.test import TestCase

from bookings.models import AvailabilityBlock, BookingInquiry, BookingNotification
from bookings.services import cancel_booking, confirm_booking, send_booking_confirmation
from property.models import Property


class BookingAvailabilityEngineTests(TestCase):
    def setUp(self):
        self.property = Property.objects.create(name="Test Villa")

    def test_pending_website_booking_does_not_make_dates_unavailable(self):
        BookingInquiry.objects.create(
            full_name="Jane Guest",
            phone="+94 77 123 4567",
            email="jane@example.com",
            check_in=datetime.date(2026, 9, 20),
            check_out=datetime.date(2026, 9, 23),
            adults=2,
        )

        self.assertTrue(
            BookingInquiry.is_date_range_available(
                self.property,
                datetime.date(2026, 9, 20),
                datetime.date(2026, 9, 24),
            )
        )

    def test_confirmed_booking_blocks_dates(self):
        booking = BookingInquiry.objects.create(
            full_name="Confirmed Guest", phone="94770000000", email="guest@example.com",
            check_in=datetime.date(2026, 9, 20), check_out=datetime.date(2026, 9, 23),
            adults=2, booking_status=BookingInquiry.STATUS_CONFIRMED,
        )
        self.assertFalse(BookingInquiry.is_date_range_available(self.property, booking.check_in, datetime.date(2026, 9, 24)))

    def test_overlapping_confirmation_is_rejected_and_booking_stays_pending(self):
        BookingInquiry.objects.create(
            full_name="First Guest", phone="94770000000", email="first@example.com",
            check_in=datetime.date(2026, 9, 20), check_out=datetime.date(2026, 9, 23),
            booking_status=BookingInquiry.STATUS_CONFIRMED,
        )
        booking = BookingInquiry.objects.create(
            full_name="Second Guest", phone="94771111111", email="second@example.com",
            check_in=datetime.date(2026, 9, 22), check_out=datetime.date(2026, 9, 25),
        )
        with self.assertRaisesMessage(ValueError, "selected dates are no longer available"):
            confirm_booking(booking)
        booking.refresh_from_db()
        self.assertEqual(booking.booking_status, BookingInquiry.STATUS_PENDING)

    def test_cancelled_booking_is_available_again(self):
        booking = BookingInquiry.objects.create(
            full_name="Guest", phone="94770000000", email="guest@example.com",
            check_in=datetime.date(2026, 9, 20), check_out=datetime.date(2026, 9, 23),
            booking_status=BookingInquiry.STATUS_CONFIRMED,
        )
        cancel_booking(booking)
        self.assertTrue(BookingInquiry.is_date_range_available(self.property, booking.check_in, booking.check_out))

    def test_unconfigured_whatsapp_is_logged_as_failed(self):
        booking = BookingInquiry.objects.create(
            full_name="Guest", phone="94770000000", email="guest@example.com",
            check_in=datetime.date(2026, 10, 1), check_out=datetime.date(2026, 10, 4),
        )
        notification = send_booking_confirmation(booking)
        self.assertEqual(notification.message_status, BookingNotification.STATUS_FAILED)

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
