import datetime
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
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

    def test_confirmed_booking_cannot_be_confirmed_again(self):
        booking = BookingInquiry.objects.create(
            full_name="Guest", phone="94770000000", email="guest@example.com",
            check_in=datetime.date(2026, 11, 1), check_out=datetime.date(2026, 11, 4),
            booking_status=BookingInquiry.STATUS_CONFIRMED,
        )
        with self.assertRaisesMessage(ValueError, "Only pending bookings can be confirmed."):
            confirm_booking(booking)

    @patch("bookings.whatsapp.WhatsAppProvider.send_text", return_value=(True, '{"messages": []}', datetime.datetime(2026, 9, 4, tzinfo=datetime.timezone.utc)))
    def test_successful_whatsapp_is_logged_with_sent_timestamp(self, send_text):
        booking = BookingInquiry.objects.create(
            full_name="Guest", phone="94770000000", email="guest@example.com",
            check_in=datetime.date(2026, 12, 1), check_out=datetime.date(2026, 12, 4),
        )
        notification = send_booking_confirmation(booking)
        self.assertEqual(notification.message_status, BookingNotification.STATUS_SENT)
        self.assertIsNotNone(notification.sent_at)
        send_text.assert_called_once()

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


class BookingAdminWorkflowTests(TestCase):
    def setUp(self):
        self.property = Property.objects.create(name="Test Villa")
        self.booking = BookingInquiry.objects.create(
            full_name="Guest", phone="94770000000", email="guest@example.com",
            check_in=datetime.date(2026, 12, 10), check_out=datetime.date(2026, 12, 13),
        )
        self.action_url = reverse("bookings:booking_action", args=[self.booking.pk, "confirm"])

    def test_anonymous_user_cannot_confirm_booking(self):
        response = self.client.post(self.action_url)
        self.booking.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.booking.booking_status, BookingInquiry.STATUS_PENDING)

    def test_get_request_does_not_change_booking_status(self):
        user = get_user_model().objects.create_user(username="owner", password="secret", is_staff=True)
        self.client.force_login(user)
        response = self.client.get(self.action_url)
        self.booking.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.booking.booking_status, BookingInquiry.STATUS_PENDING)

    def test_staff_post_confirms_booking_and_logs_notification_failure(self):
        user = get_user_model().objects.create_user(username="owner", password="secret", is_staff=True)
        self.client.force_login(user)
        response = self.client.post(self.action_url)
        self.booking.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.booking.booking_status, BookingInquiry.STATUS_CONFIRMED)
        self.assertEqual(self.booking.notifications.count(), 1)
