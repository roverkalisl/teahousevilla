from django.contrib.sitemaps import Sitemap
from django.http import HttpResponse
from django.urls import reverse

from property.models import Room

CANONICAL_DOMAIN = "teahousevillagalle.com"
CANONICAL_ORIGIN = f"https://{CANONICAL_DOMAIN}"


def robots_txt(request):
    content = "\n".join(
        (
            "User-agent: *",
            "Allow: /",
            "Disallow: /admin/",
            "Disallow: /admin-login/",
            "Disallow: /admin-logout/",
            "Disallow: /admin-dashboard/",
            "Disallow: /manage/",
            "Disallow: /booking/success/",
            "Disallow: /api/",
            f"Sitemap: {CANONICAL_ORIGIN}/sitemap.xml",
            "",
        )
    )
    return HttpResponse(content, content_type="text/plain")


class CanonicalSitemap(Sitemap):
    protocol = "https"

    def get_domain(self, site=None):
        return CANONICAL_DOMAIN


class PublicPagesSitemap(CanonicalSitemap):
    def items(self):
        return (
            "property:home",
            "property:about",
            "property:property_detail",
            "property:room_list",
            "property:gallery",
            "property:contact",
        )

    def location(self, item):
        return reverse(item)


class PublicRoomsSitemap(CanonicalSitemap):
    def items(self):
        return Room.objects.filter(active=True).select_related("villa")

    def location(self, item):
        return item.get_absolute_url()
