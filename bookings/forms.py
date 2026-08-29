import datetime

from django import forms

from property.models import Property

from .models import AvailabilityBlock, BookingInquiry

INPUT_CLASSES = "input-field"


class BookingInquiryForm(forms.ModelForm):
    class Meta:
        model = BookingInquiry
        fields = [
            "full_name",
            "phone",
            "whatsapp_number",
            "email",
            "check_in",
            "check_out",
            "adults",
            "children",
            "message",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "Your full name"}),
            "phone": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "+94 77 123 4567"}),
            "whatsapp_number": forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "If different from phone"}),
            "email": forms.EmailInput(attrs={"class": INPUT_CLASSES, "placeholder": "you@example.com"}),
            "check_in": forms.DateInput(attrs={"class": INPUT_CLASSES, "type": "date"}),
            "check_out": forms.DateInput(attrs={"class": INPUT_CLASSES, "type": "date"}),
            "adults": forms.NumberInput(attrs={"class": INPUT_CLASSES, "min": 1}),
            "children": forms.NumberInput(attrs={"class": INPUT_CLASSES, "min": 0}),
            "message": forms.Textarea(attrs={"class": INPUT_CLASSES, "rows": 4, "placeholder": "Special requests, questions, etc."}),
        }

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get("check_in")
        check_out = cleaned_data.get("check_out")

        if check_in and check_in < datetime.date.today():
            self.add_error("check_in", "Check-in date can't be in the past.")
        if check_in and check_out and check_out <= check_in:
            self.add_error("check_out", "Check-out date must be after check-in date.")

        if check_in and check_out and check_in < datetime.date.today() or (check_in and check_out and check_out <= check_in):
            return cleaned_data

        property_obj = Property.objects.first()
        if property_obj and not BookingInquiry.is_date_range_available(property_obj, check_in, check_out):
            self.add_error("check_in", "Selected dates are unavailable. Please choose another date range.")
            self.add_error("check_out", "Selected dates are unavailable. Please choose another date range.")

        return cleaned_data
