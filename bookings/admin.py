from django.contrib import admin

from .models import BookingInquiry


@admin.register(BookingInquiry)
class BookingInquiryAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "check_in",
        "check_out",
        "adults",
        "children",
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
        "message",
        "estimated_total",
        "created_at",
    )
