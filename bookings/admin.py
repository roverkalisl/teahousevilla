from django.contrib import admin

from .models import AvailabilityBlock, BookingInquiry, BookingNotification, CalendarSync, ExternalCalendarEvent, OTAAvailabilitySyncStatus


@admin.register(AvailabilityBlock)
class AvailabilityBlockAdmin(admin.ModelAdmin):
    list_display = ("villa", "source", "start_date", "end_date", "active", "notes")
    list_filter = ("source", "active", "villa")
    search_fields = ("notes", "villa__name")
    ordering = ("start_date", "end_date")


@admin.register(OTAAvailabilitySyncStatus)
class OTAAvailabilitySyncStatusAdmin(admin.ModelAdmin):
    list_display = ("villa", "source", "status", "last_synced_at", "last_error")
    list_filter = ("source", "status", "villa")
    search_fields = ("villa__name", "last_error")
    readonly_fields = ("villa", "source", "last_synced_at", "status", "last_error", "updated_at")

    actions = ["sync_selected_now"]

    @admin.action(description="Sync selected OTA sources now")
    def sync_selected_now(self, request, queryset):
        from .services import sync_ota_source

        for status in queryset:
            sync_ota_source(status.villa, status.source)


@admin.register(CalendarSync)
class CalendarSyncAdmin(admin.ModelAdmin):
    list_display = ("villa", "platform", "is_active", "last_sync_status", "last_synced_at")
    list_filter = ("platform", "is_active", "last_sync_status")
    search_fields = ("villa__name", "ical_url", "last_error")


@admin.register(ExternalCalendarEvent)
class ExternalCalendarEventAdmin(admin.ModelAdmin):
    list_display = ("villa", "platform", "external_event_id", "start_date", "end_date", "last_synced_at")
    list_filter = ("platform", "villa")
    search_fields = ("external_event_id", "summary", "villa__name")


@admin.register(BookingInquiry)
class BookingInquiryAdmin(admin.ModelAdmin):
    list_display = (
        "booking_reference",
        "full_name",
        "check_in",
        "check_out",
        "adults",
        "children",
        "guest_count",
        "estimated_total",
        "contacted",
        "created_at",
        "booking_status",
        "booking_source",
    )
    list_filter = ("booking_status", "booking_source", "contacted", "check_in")
    search_fields = ("booking_reference", "full_name", "email", "phone")
    list_editable = ("contacted",)
    readonly_fields = (
        "full_name",
        "phone",
        "whatsapp_number",
        "email",
        "check_in",
        "check_out",
        "adults",
        "children",
        "guest_count",
        "message",
        "estimated_total",
        "total_amount",
        "booking_reference",
        "booking_status",
        "booking_source",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (None, {"fields": ("booking_reference", "booking_status", "booking_source", "full_name", "phone", "whatsapp_number", "email")}),
        ("Stay", {"fields": ("check_in", "check_out", "adults", "children", "message", "estimated_total", "total_amount")}),
        ("Tracking", {"fields": ("contacted", "created_at", "updated_at")}),
    )


@admin.register(BookingNotification)
class BookingNotificationAdmin(admin.ModelAdmin):
    list_display = ("booking", "notification_type", "channel", "recipient", "message_status", "sent_at")
    list_filter = ("notification_type", "message_status", "channel")
    search_fields = ("booking__booking_reference", "recipient")
    readonly_fields = [field.name for field in BookingNotification._meta.fields]
