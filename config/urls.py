from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView

from bookings import views as booking_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("property.urls")),
    path("admin-login/", booking_views.admin_login, name="admin_login_alias"),
    path("admin-logout/", booking_views.admin_logout, name="admin_logout_alias"),
    path("admin-dashboard/", booking_views.dashboard, name="dashboard_alias"),
    path("admin-dashboard/bookings/", booking_views.manage_bookings, name="dashboard_bookings_alias"),
    path("admin-dashboard/bookings/<int:pk>/", booking_views.booking_detail, name="dashboard_booking_detail_alias"),
    path("admin-dashboard/calendar/", booking_views.calendar, name="calendar_alias"),
    path("admin-dashboard/villa/", booking_views.villa_info, name="villa_info_alias"),
    path("admin-dashboard/gallery/", booking_views.gallery, name="gallery_admin_alias"),
    path("admin-dashboard/pricing/", booking_views.pricing, name="pricing_alias"),
    path("admin-dashboard/settings/", booking_views.settings_page, name="settings_alias"),
    path("booking/", include(("bookings.urls", "bookings"), namespace="bookings")),
    path("bookings/", RedirectView.as_view(pattern_name="bookings:inquire", permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
