import datetime

from django.conf import settings
from django.utils import timezone

from property.models import Property

from .models import AvailabilityBlock, BookingInquiry, BookingNotification, OTAAvailabilitySyncStatus
from .whatsapp import WhatsAppProvider


def confirm_booking(booking):
    from django.db import transaction

    with transaction.atomic():
        locked = BookingInquiry.objects.select_for_update().get(pk=booking.pk)
        if locked.booking_status != BookingInquiry.STATUS_PENDING:
            raise ValueError("Only pending bookings can be confirmed.")
        property_obj = Property.objects.select_for_update().first()
        if not BookingInquiry.is_date_range_available(property_obj, locked.check_in, locked.check_out):
            raise ValueError("Unable to confirm this booking. The selected dates are no longer available.")
        locked.booking_status = BookingInquiry.STATUS_CONFIRMED
        locked.save(update_fields=["booking_status", "updated_at"])
    return locked


def cancel_booking(booking):
    if booking.booking_status == BookingInquiry.STATUS_CANCELLED:
        return booking
    booking.booking_status = BookingInquiry.STATUS_CANCELLED
    booking.save(update_fields=["booking_status", "updated_at"])
    return booking


def _send_whatsapp(booking, notification_type, message):
    notification = BookingNotification.objects.create(booking=booking, notification_type=notification_type, recipient=booking.whatsapp_contact_number, message=message)
    sent, provider_response, sent_at = WhatsAppProvider().send_text(notification.recipient, message)
    notification.message_status = BookingNotification.STATUS_SENT if sent else BookingNotification.STATUS_FAILED
    notification.provider_response = provider_response
    notification.sent_at = sent_at
    notification.save(update_fields=["message_status", "provider_response", "sent_at"])
    return notification


def send_booking_confirmation(booking):
    message = (f"Tea House Villa\n\nDear {booking.full_name},\n\nYour booking has been CONFIRMED.\n\nBooking Reference: {booking.booking_reference}\n"
               f"Check-in: {booking.check_in:%d %B %Y}\nCheck-out: {booking.check_out:%d %B %Y}\nGuests: {booking.guest_count}\n\nThank you for choosing Tea House Villa. We look forward to welcoming you!")
    return _send_whatsapp(booking, BookingNotification.TYPE_CONFIRMED, message)


def send_booking_cancellation(booking):
    message = (f"Tea House Villa\n\nDear {booking.full_name},\n\nWe regret to inform you that your booking request has been cancelled.\n\nBooking Reference: {booking.booking_reference}\n\nPlease contact Tea House Villa if you require assistance.")
    return _send_whatsapp(booking, BookingNotification.TYPE_CANCELLED, message)


def _get_or_create_sync_status(villa: Property, source: str):
    return OTAAvailabilitySyncStatus.objects.get_or_create(villa=villa, source=source)[0]


def sync_ota_source(villa: Property, source: str):
    if source not in {OTAAvailabilitySyncStatus.AIRBNB, OTAAvailabilitySyncStatus.BOOKING_COM}:
        return None

    status = _get_or_create_sync_status(villa, source)
    try:
        if not getattr(settings, "OTA_SYNC_ENABLED", False):
            status.status = OTAAvailabilitySyncStatus.STATUS_FAILED
            status.last_error = "OTA sync is not enabled in settings. Configure an official provider integration to enable synchronization."
            status.save(update_fields=["status", "last_error", "updated_at"])
            return status

        status.last_synced_at = timezone.now()
        status.status = OTAAvailabilitySyncStatus.STATUS_SUCCESS
        status.last_error = ""
        status.save(update_fields=["last_synced_at", "status", "last_error", "updated_at"])
        return status
    except Exception as exc:  # pragma: no cover - provider-layer integration hook
        status.status = OTAAvailabilitySyncStatus.STATUS_FAILED
        status.last_error = str(exc)
        status.save(update_fields=["status", "last_error", "updated_at"])
        return status


def refresh_availability_from_ota(villa: Property | None = None):
    property_obj = villa or Property.objects.first()
    if not property_obj:
        return []
    return [sync_ota_source(property_obj, source) for source in [OTAAvailabilitySyncStatus.AIRBNB, OTAAvailabilitySyncStatus.BOOKING_COM]]


def export_direct_booking_to_connected_channels(booking: BookingInquiry):
    if not booking or not booking.pk:
        return []

    property_obj = Property.objects.first()
    if not property_obj:
        return []

    export_results = []
    for source in [OTAAvailabilitySyncStatus.AIRBNB, OTAAvailabilitySyncStatus.BOOKING_COM]:
        status = _get_or_create_sync_status(property_obj, source)
        if not getattr(settings, "OTA_EXPORT_ENABLED", False):
            export_results.append({
                "source": source,
                "status": "not_configured",
                "message": "Official OTA export is not configured for this source.",
                "guest_count": booking.guest_count,
            })
            continue

        export_results.append({
            "source": source,
            "status": "exported",
            "check_in": booking.check_in.isoformat(),
            "check_out": booking.check_out.isoformat(),
            "guest_count": booking.guest_count,
            "booking_id": booking.pk,
            "message": "Direct booking export queued; provider-specific sync must be configured with a supported channel manager or API.",
        })

    return export_results


def create_manual_block(villa: Property, start_date: datetime.date, end_date: datetime.date, notes: str = "", source: str = AvailabilityBlock.MANUAL):
    if end_date <= start_date:
        raise ValueError("Manual block end date must be after the start date.")
    return AvailabilityBlock.objects.create(
        villa=villa,
        source=source,
        start_date=start_date,
        end_date=end_date,
        notes=notes,
        active=True,
    )
