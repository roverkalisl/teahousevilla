from .models import Property


def site_property(request):
    """Makes the singleton Property available as `site_property` in every template."""
    return {"site_property": Property.objects.first()}
