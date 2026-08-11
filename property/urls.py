from django.urls import path

from . import views

app_name = "property"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("rooms/", views.room_list, name="room_list"),
    path("rooms/<slug:slug>/", views.room_detail, name="room_detail"),
    path("gallery/", views.gallery, name="gallery"),
    path("contact/", views.contact, name="contact"),
]
