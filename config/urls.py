from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic.base import RedirectView

from .seo import PublicPagesSitemap, PublicRoomsSitemap, robots_txt

urlpatterns = [
    path("robots.txt", robots_txt, name="robots_txt"),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": {"pages": PublicPagesSitemap, "rooms": PublicRoomsSitemap}},
        name="sitemap",
    ),
    path("admin/", admin.site.urls),
    path("", include("property.urls")),
    path("", include(("bookings.admin_urls", "bookings"), namespace="bookings")),
    path("booking/", include("bookings.urls")),
    path("bookings/", RedirectView.as_view(pattern_name="bookings_public:inquire", permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
