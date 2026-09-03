from django.urls import path

from . import views

app_name = "bookings"

urlpatterns = [
    path("admin-login/", views.admin_login, name="admin_login"),
    path("admin-logout/", views.admin_logout, name="admin_logout"),
    path("admin-dashboard/", views.dashboard, name="dashboard"),
    path("admin-dashboard/bookings/", views.manage_bookings, name="dashboard_bookings"),
    path("admin-dashboard/bookings/<int:pk>/", views.booking_detail, name="dashboard_booking_detail"),
    path("admin-dashboard/calendar/", views.calendar, name="calendar"),
    path("admin-dashboard/villa/", views.villa_info, name="villa_info"),
    path("admin-dashboard/gallery/", views.gallery, name="gallery_admin"),
    path("admin-dashboard/pricing/", views.pricing, name="pricing"),
    path("admin-dashboard/settings/", views.settings_page, name="settings"),
    path("", views.inquire, name="inquire"),
    path("success/<int:pk>/", views.inquiry_success, name="inquiry_success"),
    path("manage/", views.manage_bookings, name="manage_list"),
    path("manage/<int:pk>/", views.booking_detail, name="manage_detail"),
    path("manage/<int:pk>/<str:action>/", views.booking_action, name="booking_action"),
    path("manage/notification/<int:pk>/resend/", views.resend_notification, name="resend_notification"),
]
