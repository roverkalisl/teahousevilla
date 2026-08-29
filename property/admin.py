from django.contrib import admin
from django.utils.html import format_html

from .models import Attraction, Facility, Media, Price, Property, Room, Testimonial


def thumb(obj):
    if getattr(obj, "image", None):
        return format_html('<img src="{}" style="height:50px;border-radius:4px;" />', obj.image.url)
    return "—"


thumb.short_description = "Preview"


class MediaInline(admin.TabularInline):
    model = Media
    extra = 1
    fields = ("media_type", "image", "video_url", "caption", "category", "is_cover", "display_order", "active")


class PriceInline(admin.TabularInline):
    model = Price
    extra = 1
    fields = ("price_type", "start_date", "end_date", "amount", "notes", "active")


class RoomInline(admin.StackedInline):
    model = Room
    extra = 0
    fields = ("name", "capacity", "bed_type", "bathroom_info", "has_ac", "size_sqm", "facilities", "active", "display_order")
    filter_horizontal = ("facilities",)
    show_change_link = True


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    inlines = [PriceInline, MediaInline]
    fieldsets = (
        ("Overview", {"fields": ("name", "tagline", "short_description", "full_description", "hero_image", "hero_video_url")}),
        ("Location", {"fields": ("address", "google_maps_url", "google_maps_embed_url")}),
        ("Capacity", {"fields": ("max_guests", "bedrooms", "bathrooms", "property_size_sqm")}),
        ("Stay Policy", {"fields": ("check_in_time", "check_out_time", "house_rules", "cancellation_policy")}),
        ("Contact", {"fields": ("phone_number", "whatsapp_number", "email")}),
        ("Social Media", {"fields": ("facebook_url", "instagram_url", "tiktok_url", "youtube_url")}),
        ("Also Listed On", {"fields": ("airbnb_url", "booking_com_url")}),
        ("Pricing Fallback", {"fields": ("starting_price_override",)}),
    )

    def has_add_permission(self, request):
        # Singleton: only one Property row should exist.
        return not Property.objects.exists()


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "villa", "capacity", "bed_type", "has_ac", "active", "display_order")
    list_filter = ("active", "has_ac", "villa")
    search_fields = ("name", "description")
    filter_horizontal = ("facilities",)
    prepopulated_fields = {"slug": ("name",)}
    inlines = [MediaInline]

    def save_formset(self, request, form, formset, change):
        """Automatically set villa for inline media from the room's villa."""
        if formset.model == Media:
            instances = formset.save(commit=False)
            for instance in instances:
                if not instance.villa_id:
                    instance.villa = form.instance.villa
                instance.save()
            formset.save_m2m()
        else:
            formset.save()


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ("name", "icon", "active", "display_order")
    list_filter = ("active",)
    search_fields = ("name",)
    list_editable = ("display_order", "active")


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = (thumb, "caption", "media_type", "category", "villa", "room", "is_cover", "active", "display_order")
    list_filter = ("media_type", "category", "active", "is_cover")
    search_fields = ("caption",)
    list_editable = ("display_order", "active")


@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    list_display = ("villa", "price_type", "amount", "start_date", "end_date", "active")
    list_filter = ("price_type", "active")


@admin.register(Attraction)
class AttractionAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "distance_text", "villa", "active", "display_order")
    list_filter = ("category", "active")
    search_fields = ("name", "description")
    list_editable = ("display_order", "active")


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("guest_name", "rating", "source", "stay_date", "active", "display_order")
    list_filter = ("source", "rating", "active")
    search_fields = ("guest_name", "review_text")
    list_editable = ("display_order", "active")
