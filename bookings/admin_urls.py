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
    path("admin-dashboard/reviews/", views.manage_reviews, name="manage_reviews"),
    path("admin-dashboard/reviews/add/", views.add_review, name="add_review"),
    path("admin-dashboard/reviews/<int:pk>/edit/", views.edit_review, name="edit_review"),
    path("admin-dashboard/reviews/<int:pk>/delete/", views.delete_review, name="delete_review"),
    path("admin-dashboard/reviews/<int:pk>/toggle/", views.toggle_review_active, name="toggle_review_active"),
    path("admin-dashboard/settings/", views.settings_page, name="settings"),
    path("admin-dashboard/settings/ota/<str:source>/sync/", views.sync_ota, name="sync_ota"),
    path("manage/", views.manage_bookings, name="manage_list"),
    path("manage/<int:pk>/", views.booking_detail, name="manage_detail"),
    path("manage/<int:pk>/<str:action>/", views.booking_action, name="booking_action"),
    path("manage/notification/<int:pk>/resend/", views.resend_notification, name="resend_notification"),
]
