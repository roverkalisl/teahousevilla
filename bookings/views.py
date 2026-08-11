import datetime
from urllib.parse import quote

from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render

from property.models import Property

from .forms import BookingInquiryForm
from .models import BookingInquiry


def inquire(request):
    site = Property.objects.first()
    initial = {}
    if request.GET.get("check_in"):
        initial["check_in"] = request.GET["check_in"]
    if request.GET.get("check_out"):
        initial["check_out"] = request.GET["check_out"]

    if request.method == "POST":
        form = BookingInquiryForm(request.POST)
        if form.is_valid():
            inquiry = form.save(commit=False)
            if site:
                nightly_rate = site.get_starting_price()
                if nightly_rate:
                    inquiry.estimated_total = nightly_rate * inquiry.nights
            inquiry.save()
            _notify_owner(site, inquiry)
            return redirect("bookings:inquiry_success", pk=inquiry.pk)
    else:
        form = BookingInquiryForm(initial=initial)

    return render(request, "bookings/inquire.html", {"property": site, "form": form})


def inquiry_success(request, pk):
    inquiry = get_object_or_404(BookingInquiry, pk=pk)
    site = Property.objects.first()

    whatsapp_link = ""
    if site and site.whatsapp_link:
        message_lines = [
            "New Villa Booking Inquiry",
            f"Guest: {inquiry.full_name}",
            f"Check-in: {inquiry.check_in:%d %B %Y}",
            f"Check-out: {inquiry.check_out:%d %B %Y}",
            f"Guests: {inquiry.adults + inquiry.children}",
        ]
        if inquiry.estimated_total:
            message_lines.append(f"Estimated Total: Rs. {inquiry.estimated_total}")
        message = quote("\n".join(message_lines))
        whatsapp_link = f"{site.whatsapp_link}?text={message}"

    context = {"property": site, "inquiry": inquiry, "whatsapp_link": whatsapp_link}
    return render(request, "bookings/inquiry_success.html", context)


def _notify_owner(site, inquiry):
    if not site or not site.email:
        return
    subject = f"New Booking Inquiry — {inquiry.full_name} ({inquiry.check_in} to {inquiry.check_out})"
    body = (
        f"Guest: {inquiry.full_name}\n"
        f"Phone: {inquiry.phone}\n"
        f"WhatsApp: {inquiry.whatsapp_contact_number}\n"
        f"Email: {inquiry.email}\n\n"
        f"Check-in: {inquiry.check_in}\n"
        f"Check-out: {inquiry.check_out} ({inquiry.nights} nights)\n"
        f"Guests: {inquiry.adults} adults, {inquiry.children} children\n"
        f"Estimated Total: {inquiry.estimated_total or 'N/A'}\n\n"
        f"Message:\n{inquiry.message or '(none)'}"
    )
    send_mail(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [site.email],
        fail_silently=True,
    )
