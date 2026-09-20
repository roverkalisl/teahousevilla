from django.shortcuts import get_object_or_404, render
from django.db.models import Avg, Count, Prefetch
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import Attraction, Facility, Media, Property, Room, Testimonial, PropertyAmenity, PropertyView, BedConfiguration


def _get_property():
    return Property.objects.first()


def home(request):
    site = _get_property()

    # Calculate review statistics
    active_reviews = Testimonial.objects.filter(active=True)
    review_stats = active_reviews.aggregate(
        avg_rating=Avg("rating"),
        total_count=Count("id")
    )

    context = {
        "property": site,
        "rooms": Room.objects.filter(active=True)[:3] if site else [],
        "facilities": Facility.objects.filter(active=True)[:8],
        "gallery_preview": Media.objects.filter(active=True, media_type=Media.IMAGE)[:8],
        "hero_slides": Media.objects.filter(active=True, media_type=Media.IMAGE, room__isnull=True)[:6],
        "featured_video": Media.objects.filter(active=True, media_type=Media.VIDEO).first(),
        "starting_price": site.get_starting_price() if site else None,
        "attractions": Attraction.objects.filter(active=True)[:6],
        "testimonials": Testimonial.objects.filter(active=True)[:6],
        "featured_reviews": active_reviews[:3],
        "all_reviews_count": review_stats.get("total_count", 0),
        "average_rating": round(review_stats.get("avg_rating", 0), 1) if review_stats.get("avg_rating") else 0,
    }
    return render(request, "property/home.html", context)


def about(request):
    site = _get_property()
    context = {
        "property": site,
        "facilities": Facility.objects.filter(active=True),
        "attractions": Attraction.objects.filter(active=True),
    }
    return render(request, "property/about.html", context)


def room_list(request):
    context = {
        "property": _get_property(),
        "rooms": Room.objects.filter(active=True),
    }
    return render(request, "property/room_list.html", context)


def room_detail(request, slug):
    room = get_object_or_404(Room, slug=slug, active=True)
    context = {
        "property": _get_property(),
        "room": room,
        "room_media": room.media.filter(active=True),
    }
    return render(request, "property/room_detail.html", context)


def gallery(request):
    context = {
        "property": _get_property(),
        "images": Media.objects.filter(active=True, media_type=Media.IMAGE),
        "videos": Media.objects.filter(active=True, media_type=Media.VIDEO),
        "categories": Media.CATEGORY_CHOICES,
    }
    return render(request, "property/gallery.html", context)


def contact(request):
    context = {"property": _get_property()}
    return render(request, "property/contact.html", context)


def property_detail(request):
    """Comprehensive property detail page."""
    site = _get_property()
    if not site:
        return render(request, "property/property_not_found.html", {"site": site})

    # Prefetch related data for performance
    bed_configs_prefetch = Prefetch(
        'bed_configurations',
        BedConfiguration.objects.filter(active=True).select_related('bed_type').order_by('display_order')
    )
    rooms = Room.objects.filter(villa=site, active=True).prefetch_related(
        bed_configs_prefetch,
        'media',
        'facilities'
    ).order_by('display_order')

    # Calculate review statistics
    active_reviews = Testimonial.objects.filter(villa=site, active=True)
    review_stats = active_reviews.aggregate(
        avg_rating=Avg("rating"),
        total_count=Count("id")
    )

    # Categorize media
    media_by_category = {}
    for choice_val, choice_label in Media.CATEGORY_CHOICES:
        media_by_category[choice_val] = Media.objects.filter(
            villa=site, active=True, media_type=Media.IMAGE, category=choice_val
        ).order_by('display_order')

    context = {
        "property": site,
        "rooms": rooms,
        "amenities": PropertyAmenity.objects.filter(
            villa=site, active=True
        ).order_by('category', 'display_order'),
        "views": PropertyView.objects.filter(villa=site, active=True).order_by('display_order'),
        "facilities": Facility.objects.filter(active=True).order_by('display_order'),
        "gallery_by_category": media_by_category,
        "attractions": Attraction.objects.filter(villa=site, active=True).order_by('display_order'),
        "testimonials": active_reviews.order_by('-stay_date', '-id')[:6],
        "all_reviews_count": review_stats.get("total_count", 0),
        "average_rating": round(review_stats.get("avg_rating", 0), 1) if review_stats.get("avg_rating") else 0,
        "hero_slides": Media.objects.filter(active=True, media_type=Media.IMAGE, room__isnull=True)[:6],
    }
    return render(request, "property/property_detail.html", context)


@require_http_methods(["GET"])
def api_reviews(request):
    """API endpoint to fetch all active reviews as JSON."""
    reviews = Testimonial.objects.filter(active=True).order_by("display_order", "-id").values(
        "id", "guest_name", "rating", "review_text", "source", "stay_date", "guest_photo"
    )

    reviews_list = []
    for review in reviews:
        reviews_list.append({
            "id": review["id"],
            "guest_name": review["guest_name"],
            "rating": review["rating"],
            "review_text": review["review_text"],
            "source": review["source"],
            "stay_date": review["stay_date"].isoformat() if review["stay_date"] else None,
            "guest_photo": request.build_absolute_uri(review["guest_photo"]) if review["guest_photo"] else None,
        })

    return JsonResponse({
        "success": True,
        "count": len(reviews_list),
        "reviews": reviews_list,
    })
