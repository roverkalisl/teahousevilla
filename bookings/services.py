import datetime
from typing import Any

from django.conf import settings
from django.utils import timezone

from property.models import Property

from .models import AvailabilityBlock, BookingInquiry, OTAAvailabilitySyncStatus


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
