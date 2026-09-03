import datetime
from urllib.parse import quote

from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from property.models import Media, Price, Property

from .forms import AdminLoginForm, BookingInquiryForm
from .models import AvailabilityBlock, BookingInquiry, BookingNotification, OTAAvailabilitySyncStatus
from .services import cancel_booking, confirm_booking, send_booking_cancellation, send_booking_confirmation


def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("bookings:dashboard")
    form = AdminLoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.user)
        return redirect(request.GET.get("next") or "bookings:dashboard")
    return render(request, "admin_dashboard/login.html", {"form": form})


def admin_logout(request):
    logout(request)
    return redirect("bookings:admin_login")


def _staff_required(view):
    return user_passes_test(lambda user: user.is_staff, login_url="bookings:admin_login")(login_required(view))


@_staff_required
def dashboard(request):
    today = datetime.date.today()
    bookings = BookingInquiry.objects.all()
    return render(request, "admin_dashboard/dashboard.html", {
        "property": Property.objects.first(),
        "pending_count": bookings.filter(booking_status=BookingInquiry.STATUS_PENDING).count(),
        "confirmed_count": bookings.filter(booking_status=BookingInquiry.STATUS_CONFIRMED).count(),
        "cancelled_count": bookings.filter(booking_status=BookingInquiry.STATUS_CANCELLED).count(),
        "checkins_today": bookings.filter(check_in=today, booking_status=BookingInquiry.STATUS_CONFIRMED).count(),
        "checkouts_today": bookings.filter(check_out=today, booking_status=BookingInquiry.STATUS_CONFIRMED).count(),
        "upcoming_bookings": bookings.filter(check_out__gte=today).exclude(booking_status=BookingInquiry.STATUS_CANCELLED).order_by("check_in")[:6],
    })


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


@_staff_required
def manage_bookings(request):
    bookings = BookingInquiry.objects.all()
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status")
    source = request.GET.get("source")
    if status in {choice[0] for choice in BookingInquiry.STATUS_CHOICES}:
        bookings = bookings.filter(booking_status=status)
    if source in {choice[0] for choice in BookingInquiry.SOURCE_CHOICES}:
        bookings = bookings.filter(booking_source=source)
    if query:
        bookings = bookings.filter(Q(full_name__icontains=query) | Q(booking_reference__icontains=query))
    if request.GET.get("period") == "upcoming":
        bookings = bookings.filter(check_out__gte=datetime.date.today())
    elif request.GET.get("period") == "past":
        bookings = bookings.filter(check_out__lt=datetime.date.today())
    page = Paginator(bookings.order_by("-created_at"), 10).get_page(request.GET.get("page"))
    return render(request, "admin_dashboard/bookings/booking_list.html", {"bookings": page, "active_status": status, "active_source": source, "query": query, "booking_status_choices": BookingInquiry.STATUS_CHOICES, "booking_source_choices": BookingInquiry.SOURCE_CHOICES})


@_staff_required
def booking_detail(request, pk):
    booking = get_object_or_404(BookingInquiry, pk=pk)
    return render(request, "admin_dashboard/bookings/booking_detail.html", {"booking": booking})


@_staff_required
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


@_staff_required
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


@_staff_required
def calendar(request):
    month = request.GET.get("month", datetime.date.today().strftime("%Y-%m"))
    try:
        year, month_number = [int(value) for value in month.split("-")]
        month_date = datetime.date(year, month_number, 1)
    except (TypeError, ValueError):
        month_date = datetime.date.today().replace(day=1)
    month_end = month_date.replace(day=28) + datetime.timedelta(days=4)
    blocks = AvailabilityBlock.objects.filter(active=True, start_date__lt=month_end, end_date__gt=month_date)
    bookings = BookingInquiry.objects.filter(check_in__lt=month_end, check_out__gt=month_date).exclude(booking_status=BookingInquiry.STATUS_CANCELLED)
    return render(request, "admin_dashboard/calendar.html", {"month_date": month_date, "blocks": blocks, "bookings": bookings})


@_staff_required
def villa_info(request):
    site = Property.objects.first()
    if request.method == "POST" and site:
        editable_fields = ("name", "tagline", "short_description", "full_description", "address", "phone_number", "whatsapp_number", "email", "check_in_time", "check_out_time", "max_guests", "house_rules", "google_maps_url")
        for field in editable_fields:
            if field in request.POST:
                setattr(site, field, request.POST[field])
        site.save()
        messages.success(request, "Villa information updated.")
    return render(request, "admin_dashboard/villa_info.html", {"property": site})


@_staff_required
def gallery(request):
    site = Property.objects.first()
    return render(request, "admin_dashboard/gallery.html", {"media_items": Media.objects.filter(villa=site).order_by("display_order", "id") if site else []})


@_staff_required
def pricing(request):
    site = Property.objects.first()
    return render(request, "admin_dashboard/pricing.html", {"prices": Price.objects.filter(villa=site) if site else []})


@_staff_required
def settings_page(request):
    return render(request, "admin_dashboard/settings.html", {"ota_statuses": OTAAvailabilitySyncStatus.objects.all(), "whatsapp_configured": bool(settings.WHATSAPP_ACCESS_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID), "email_configured": bool(settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD)})
