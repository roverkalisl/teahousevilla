from django.urls import path

from . import views

app_name = "bookings"

urlpatterns = [
    path("", views.inquire, name="inquire"),
    path("success/<int:pk>/", views.inquiry_success, name="inquiry_success"),
    path("manage/", views.manage_bookings, name="manage_list"),
    path("manage/<int:pk>/", views.booking_detail, name="manage_detail"),
    path("manage/<int:pk>/<str:action>/", views.booking_action, name="booking_action"),
    path("manage/notification/<int:pk>/resend/", views.resend_notification, name="resend_notification"),
]
