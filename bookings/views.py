import datetime
from urllib.parse import quote

from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from property.models import Media, Price, Property, Testimonial

from .forms import AdminLoginForm, BookingInquiryForm
from .models import AvailabilityBlock, BookingInquiry, BookingNotification, OTAAvailabilitySyncStatus
from .services import cancel_booking, confirm_booking, send_booking_cancellation, send_booking_confirmation, sync_ota_source


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
            return redirect("bookings_public:inquiry_success", pk=inquiry.pk)
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
    period = request.GET.get("period", "")
    check_in = request.GET.get("check_in", "")
    check_out = request.GET.get("check_out", "")
    if status in {choice[0] for choice in BookingInquiry.STATUS_CHOICES}:
        bookings = bookings.filter(booking_status=status)
    if source in {choice[0] for choice in BookingInquiry.SOURCE_CHOICES}:
        bookings = bookings.filter(booking_source=source)
    if query:
        bookings = bookings.filter(Q(full_name__icontains=query) | Q(booking_reference__icontains=query))
    if check_in:
        try:
            bookings = bookings.filter(check_in__gte=datetime.date.fromisoformat(check_in))
        except ValueError:
            check_in = ""
    if check_out:
        try:
            bookings = bookings.filter(check_out__lte=datetime.date.fromisoformat(check_out))
        except ValueError:
            check_out = ""
    if period == "upcoming":
        bookings = bookings.filter(check_out__gte=datetime.date.today())
    elif period == "past":
        bookings = bookings.filter(check_out__lt=datetime.date.today())
    page = Paginator(bookings.order_by("-created_at"), 10).get_page(request.GET.get("page"))
    return render(request, "admin_dashboard/bookings/booking_list.html", {"bookings": page, "active_status": status, "active_source": source, "active_period": period, "query": query, "check_in": check_in, "check_out": check_out, "booking_status_choices": BookingInquiry.STATUS_CHOICES, "booking_source_choices": BookingInquiry.SOURCE_CHOICES})


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
    site = Property.objects.first()
    blocks = AvailabilityBlock.objects.filter(villa=site, active=True, start_date__lt=month_end, end_date__gt=month_date) if site else AvailabilityBlock.objects.none()
    bookings = BookingInquiry.objects.filter(check_in__lt=month_end, check_out__gt=month_date).exclude(booking_status=BookingInquiry.STATUS_CANCELLED)
    if request.method == "POST" and site:
        action = request.POST.get("action")
        if action == "create_block":
            try:
                start_date = datetime.date.fromisoformat(request.POST["start_date"])
                end_date = datetime.date.fromisoformat(request.POST["end_date"])
                if end_date <= start_date:
                    raise ValueError
                AvailabilityBlock.objects.create(villa=site, source=AvailabilityBlock.MANUAL, start_date=start_date, end_date=end_date, notes=request.POST.get("notes", "").strip())
                messages.success(request, "Dates blocked successfully.")
            except (KeyError, ValueError):
                messages.error(request, "Enter a valid date range with an end date after the start date.")
        elif action == "release_block":
            block = get_object_or_404(AvailabilityBlock, pk=request.POST.get("block_id"), villa=site, source=AvailabilityBlock.MANUAL)
            block.active = False
            block.save(update_fields=("active", "updated_at"))
            messages.success(request, "Blocked dates released.")
        return redirect(f"{request.path}?month={month_date:%Y-%m}")
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
    if request.method == "POST" and site:
        action = request.POST.get("action")
        if action == "upload":
            image = request.FILES.get("image")
            if image:
                Media.objects.create(villa=site, image=image, caption=request.POST.get("caption", "").strip(), category=request.POST.get("category", Media.CATEGORY_CHOICES[0][0]), display_order=request.POST.get("display_order") or 0, is_cover=request.POST.get("is_cover") == "on")
                messages.success(request, "Photo uploaded.")
            else:
                messages.error(request, "Choose a photo to upload.")
        elif action == "delete":
            item = get_object_or_404(Media, pk=request.POST.get("media_id"), villa=site)
            item.delete()
            messages.success(request, "Photo deleted.")
        return redirect("bookings:gallery_admin")
    return render(request, "admin_dashboard/gallery.html", {"media_items": Media.objects.filter(villa=site).order_by("display_order", "id") if site else []})


@_staff_required
def pricing(request):
    site = Property.objects.first()
    if request.method == "POST" and site:
        action = request.POST.get("action")
        if action == "save":
            price = get_object_or_404(Price, pk=request.POST.get("price_id"), villa=site) if request.POST.get("price_id") else Price(villa=site)
            price.price_type = request.POST.get("price_type", Price.STANDARD)
            price.amount = request.POST.get("amount")
            price.start_date = request.POST.get("start_date") or None
            price.end_date = request.POST.get("end_date") or None
            price.notes = request.POST.get("notes", "").strip()
            price.active = request.POST.get("active") == "on"
            try:
                price.full_clean()
                price.save()
                messages.success(request, "Price saved.")
            except (TypeError, ValueError, ValidationError):
                messages.error(request, "Enter a valid price.")
        elif action == "delete":
            get_object_or_404(Price, pk=request.POST.get("price_id"), villa=site).delete()
            messages.success(request, "Price deleted.")
        return redirect("bookings:pricing")
    return render(request, "admin_dashboard/pricing.html", {"prices": Price.objects.filter(villa=site) if site else []})


@_staff_required
def settings_page(request):
    site = Property.objects.first()
    statuses = []
    if site:
        for source in (OTAAvailabilitySyncStatus.AIRBNB, OTAAvailabilitySyncStatus.BOOKING_COM):
            status, _ = OTAAvailabilitySyncStatus.objects.get_or_create(villa=site, source=source)
            statuses.append(status)
    return render(request, "admin_dashboard/settings.html", {"ota_statuses": statuses, "whatsapp_configured": bool(settings.WHATSAPP_ACCESS_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID), "email_configured": bool(settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD), "ota_sync_enabled": settings.OTA_SYNC_ENABLED})


@_staff_required
def sync_ota(request, source):
    if request.method != "POST":
        return redirect("bookings:settings")
    site = Property.objects.first()
    if site and source in {OTAAvailabilitySyncStatus.AIRBNB, OTAAvailabilitySyncStatus.BOOKING_COM}:
        sync_ota_source(site, source)
        messages.success(request, f"{source.replace('_', ' ').title()} availability sync completed.")
    return redirect("bookings:settings")


# ============================================================================
# GUEST REVIEWS MANAGEMENT
# ============================================================================

@_staff_required
def manage_reviews(request):
    """List and manage guest reviews."""
    site = Property.objects.first()
    if not site:
        testimonials = Testimonial.objects.none()
    else:
        testimonials = site.testimonials.all()

    # Filtering
    source_filter = request.GET.get("source", "").strip()
    rating_filter = request.GET.get("rating", "").strip()
    active_filter = request.GET.get("active", "").strip()
    query = request.GET.get("q", "").strip()

    if source_filter:
        testimonials = testimonials.filter(source=source_filter)
    if rating_filter:
        try:
            testimonials = testimonials.filter(rating=int(rating_filter))
        except (ValueError, TypeError):
            rating_filter = ""
    if active_filter == "active":
        testimonials = testimonials.filter(active=True)
    elif active_filter == "inactive":
        testimonials = testimonials.filter(active=False)
    if query:
        testimonials = testimonials.filter(
            Q(guest_name__icontains=query) | Q(review_text__icontains=query)
        )

    # Ordering
    order = request.GET.get("order", "-id")
    testimonials = testimonials.order_by(order)

    # Pagination
    page = Paginator(testimonials, 10).get_page(request.GET.get("page"))

    context = {
        "reviews": page,
        "source_filter": source_filter,
        "rating_filter": rating_filter,
        "active_filter": active_filter,
        "query": query,
        "source_choices": Testimonial.SOURCE_CHOICES,
        "rating_choices": Testimonial.RATING_CHOICES,
    }
    return render(request, "admin_dashboard/reviews_list.html", context)


@_staff_required
def add_review(request):
    """Add a new guest review manually."""
    site = Property.objects.first()
    if not site:
        messages.error(request, "Property not configured yet.")
        return redirect("bookings:manage_reviews")

    if request.method == "POST":
        try:
            review = Testimonial(villa=site)
            review.guest_name = request.POST.get("guest_name", "").strip()
            review.rating = int(request.POST.get("rating", 5))
            review.review_text = request.POST.get("review_text", "").strip()
            review.source = request.POST.get("source", Testimonial.GOOGLE)
            review.stay_date = request.POST.get("stay_date") or None
            review.active = request.POST.get("active") == "on"
            review.display_order = int(request.POST.get("display_order", 0))

            if request.FILES.get("guest_photo"):
                review.guest_photo = request.FILES.get("guest_photo")

            review.full_clean()
            review.save()
            messages.success(request, f"Review from {review.guest_name} added successfully.")
            return redirect("bookings:manage_reviews")
        except (ValueError, ValidationError) as e:
            messages.error(request, f"Error adding review: {e}")

    context = {
        "source_choices": Testimonial.SOURCE_CHOICES,
        "rating_choices": Testimonial.RATING_CHOICES,
    }
    return render(request, "admin_dashboard/review_form.html", context)


@_staff_required
def edit_review(request, pk):
    """Edit an existing guest review."""
    review = get_object_or_404(Testimonial, pk=pk)

    if request.method == "POST":
        try:
            review.guest_name = request.POST.get("guest_name", "").strip()
            review.rating = int(request.POST.get("rating", 5))
            review.review_text = request.POST.get("review_text", "").strip()
            review.source = request.POST.get("source", Testimonial.GOOGLE)
            review.stay_date = request.POST.get("stay_date") or None
            review.active = request.POST.get("active") == "on"
            review.display_order = int(request.POST.get("display_order", 0))

            if request.FILES.get("guest_photo"):
                review.guest_photo = request.FILES.get("guest_photo")

            review.full_clean()
            review.save()
            messages.success(request, f"Review from {review.guest_name} updated successfully.")
            return redirect("bookings:manage_reviews")
        except (ValueError, ValidationError) as e:
            messages.error(request, f"Error updating review: {e}")

    context = {
        "review": review,
        "source_choices": Testimonial.SOURCE_CHOICES,
        "rating_choices": Testimonial.RATING_CHOICES,
    }
    return render(request, "admin_dashboard/review_form.html", context)


@_staff_required
def delete_review(request, pk):
    """Delete a guest review."""
    if request.method != "POST":
        return redirect("bookings:manage_reviews")

    review = get_object_or_404(Testimonial, pk=pk)
    guest_name = review.guest_name
    review.delete()
    messages.success(request, f"Review from {guest_name} deleted successfully.")
    return redirect("bookings:manage_reviews")


@_staff_required
def toggle_review_active(request, pk):
    """Toggle a review's active status."""
    if request.method != "POST":
        return redirect("bookings:manage_reviews")

    review = get_object_or_404(Testimonial, pk=pk)
    review.active = not review.active
    review.save(update_fields=("active",))
    status = "activated" if review.active else "deactivated"
    messages.success(request, f"Review from {review.guest_name} {status}.")
    return redirect("bookings:manage_reviews")
