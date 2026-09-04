from django.urls import path

from . import views

app_name = "bookings_public"

urlpatterns = [
    path("", views.inquire, name="inquire"),
    path("success/<int:pk>/", views.inquiry_success, name="inquiry_success"),
]
