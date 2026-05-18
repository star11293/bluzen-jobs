"""
Forms for registration and profile management.

Using UserCreationForm (a ModelForm) per the architectural decision. The
RegistrationForm creates a User and the matching Profile in one atomic
transaction so we never end up with orphan users missing their profile.
"""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction

from .models import EmployerProfile, JobSeekerProfile

User = get_user_model()

# Shared Tailwind classes for text-like inputs. Applied via __init__ below.
INPUT_CLASSES = (
    "w-full px-4 py-2 border border-gray-300 rounded-md "
    "focus:ring-2 focus:ring-brand-blue focus:border-transparent "
    "outline-none transition"
)


class RegistrationForm(UserCreationForm):
    """Create a User + matching Profile in one go."""

    first_name = forms.CharField(max_length=60, required=True)
    last_name = forms.CharField(max_length=60, required=True)
    phone = forms.CharField(max_length=20, required=False)
    role = forms.ChoiceField(
        choices=[
            (User.Role.JOB_SEEKER, "Job Seeker - I'm looking for healthcare work"),
            (User.Role.EMPLOYER, "Employer - I'm hiring healthcare staff"),
        ],
        widget=forms.RadioSelect,
        initial=User.Role.JOB_SEEKER,
    )
    company_name = forms.CharField(
        max_length=200,
        required=False,
        help_text="Required if signing up as an employer.",
    )

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "phone", "role", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Auto-apply Tailwind classes to every input except the radio group.
        for name, field in self.fields.items():
            if name == "role":
                continue
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " " + INPUT_CLASSES).strip()
        # Useful autocomplete hints.
        self.fields["email"].widget.attrs.setdefault("autocomplete", "email")
        self.fields["first_name"].widget.attrs.setdefault("autocomplete", "given-name")
        self.fields["last_name"].widget.attrs.setdefault("autocomplete", "family-name")
        self.fields["phone"].widget.attrs.setdefault("autocomplete", "tel")
        self.fields["password1"].widget.attrs.setdefault("autocomplete", "new-password")
        self.fields["password2"].widget.attrs.setdefault("autocomplete", "new-password")

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("role") == User.Role.EMPLOYER:
            if not (cleaned.get("company_name") or "").strip():
                self.add_error("company_name", "Company name is required for employers.")
        return cleaned

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.phone = self.cleaned_data.get("phone", "")
        user.role = self.cleaned_data["role"]
        if commit:
            user.save()
            if user.role == User.Role.EMPLOYER:
                EmployerProfile.objects.create(
                    user=user,
                    company_name=self.cleaned_data["company_name"].strip(),
                )
            elif user.role == User.Role.JOB_SEEKER:
                JobSeekerProfile.objects.create(user=user)
        return user
