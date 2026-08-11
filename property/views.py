from django.shortcuts import get_object_or_404, render

from .models import Facility, Media, Property, Room


def _get_property():
    return Property.objects.first()


def home(request):
    site = _get_property()
    context = {
        "property": site,
        "rooms": Room.objects.filter(active=True)[:3] if site else [],
        "facilities": Facility.objects.filter(active=True)[:8],
        "gallery_preview": Media.objects.filter(active=True, media_type=Media.IMAGE)[:8],
        "featured_video": Media.objects.filter(active=True, media_type=Media.VIDEO).first(),
        "starting_price": site.get_starting_price() if site else None,
    }
    return render(request, "property/home.html", context)


def about(request):
    site = _get_property()
    context = {
        "property": site,
        "facilities": Facility.objects.filter(active=True),
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
