from django.shortcuts import render

from property.models import Property


def placeholder(request):
    context = {"property": Property.objects.first()}
    return render(request, "bookings/placeholder.html", context)
