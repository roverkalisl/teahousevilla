from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("property.urls")),
    path("booking/", include(("bookings.urls", "bookings"), namespace="bookings")),
    path("bookings/", RedirectView.as_view(pattern_name="bookings:inquire", permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
