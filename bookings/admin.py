from django.contrib import admin

from .models import AvailabilityBlock, BookingInquiry, OTAAvailabilitySyncStatus


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


@admin.register(BookingInquiry)
class BookingInquiryAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "check_in",
        "check_out",
        "adults",
        "children",
        "guest_count",
        "estimated_total",
        "contacted",
        "created_at",
    )
    list_filter = ("contacted", "check_in")
    search_fields = ("full_name", "email", "phone")
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
        "created_at",
    )
