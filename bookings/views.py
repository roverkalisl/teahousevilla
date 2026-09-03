import datetime
from urllib.parse import quote

from django.conf import settings
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render

from property.models import Property

from .forms import BookingInquiryForm
from .models import BookingInquiry, BookingNotification
from .services import cancel_booking, confirm_booking, send_booking_cancellation, send_booking_confirmation


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
                    inquiry.total_amount = inquiry.estimated_total
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


@staff_member_required
def manage_bookings(request):
    bookings = BookingInquiry.objects.all()
    status = request.GET.get("status")
    source = request.GET.get("source")
    if status in {choice[0] for choice in BookingInquiry.STATUS_CHOICES}:
        bookings = bookings.filter(booking_status=status)
    if source in {choice[0] for choice in BookingInquiry.SOURCE_CHOICES}:
        bookings = bookings.filter(booking_source=source)
    if request.GET.get("period") == "upcoming":
        bookings = bookings.filter(check_out__gte=datetime.date.today())
    elif request.GET.get("period") == "past":
        bookings = bookings.filter(check_out__lt=datetime.date.today())
    return render(request, "bookings/manage_list.html", {"bookings": bookings, "active_status": status, "active_source": source, "booking_status_choices": BookingInquiry.STATUS_CHOICES, "booking_source_choices": BookingInquiry.SOURCE_CHOICES})


@staff_member_required
def booking_detail(request, pk):
    booking = get_object_or_404(BookingInquiry, pk=pk)
    return render(request, "bookings/manage_detail.html", {"booking": booking})


@staff_member_required
def booking_action(request, pk, action):
    if request.method != "POST":
        return redirect("bookings:manage_detail", pk=pk)
    booking = get_object_or_404(BookingInquiry, pk=pk)
    if action == "confirm":
        try:
            booking = confirm_booking(booking)
            notification = send_booking_confirmation(booking)
            if notification.message_status == BookingNotification.STATUS_FAILED:
                messages.warning(request, "Booking confirmed successfully, but the WhatsApp notification failed.")
            else:
                messages.success(request, "Booking confirmed and WhatsApp notification sent.")
        except ValueError as exc:
            messages.error(request, str(exc))
    elif action == "cancel":
        booking = cancel_booking(booking)
        notification = send_booking_cancellation(booking)
        if notification.message_status == BookingNotification.STATUS_FAILED:
            messages.warning(request, "Booking cancelled, but the WhatsApp notification failed.")
        else:
            messages.success(request, "Booking cancelled and WhatsApp notification sent.")
    return redirect("bookings:manage_detail", pk=booking.pk)


@staff_member_required
def resend_notification(request, pk):
    if request.method != "POST":
        return redirect("bookings:manage_detail", pk=pk)
    notification = get_object_or_404(BookingNotification, pk=pk)
    if notification.notification_type == BookingNotification.TYPE_CONFIRMED:
        result = send_booking_confirmation(notification.booking)
    else:
        result = send_booking_cancellation(notification.booking)
    if result.message_status == BookingNotification.STATUS_SENT:
        messages.success(request, "WhatsApp notification sent.")
    else:
        messages.error(request, "WhatsApp notification failed again.")
    return redirect("bookings:manage_detail", pk=notification.booking_id)
