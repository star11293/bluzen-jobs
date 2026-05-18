"""
Forms for posting jobs and applying to them.

ModelForm-based per the architectural decision. Hand-rolled forms are how
the old build accumulated bugs.
"""
from django import forms

from .models import JobApplication, JobPosting

INPUT_CLASSES = (
    "w-full px-4 py-2 border border-gray-300 rounded-md "
    "focus:ring-2 focus:ring-brand-blue focus:border-transparent "
    "outline-none transition"
)
TEXTAREA_CLASSES = INPUT_CLASSES + " min-h-[140px] leading-relaxed"
FILE_CLASSES = (
    "block w-full text-sm text-gray-600 "
    "file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 "
    "file:text-sm file:font-semibold "
    "file:bg-brand-blue file:text-white "
    "hover:file:bg-brand-blue-dark file:cursor-pointer cursor-pointer"
)


class JobPostingForm(forms.ModelForm):
    class Meta:
        model = JobPosting
        fields = [
            "title", "description", "location", "job_type",
            "salary_min", "salary_max", "status",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 8}),
            "title": forms.TextInput(attrs={"placeholder": "e.g. Registered Nurse - ICU"}),
            "location": forms.TextInput(attrs={"placeholder": "e.g. Baltimore, MD"}),
            "salary_min": forms.NumberInput(attrs={"placeholder": "0", "step": "1000"}),
            "salary_max": forms.NumberInput(attrs={"placeholder": "0", "step": "1000"}),
        }
        help_texts = {
            "status": "Published = visible immediately. Draft = saved but hidden.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = TEXTAREA_CLASSES if isinstance(field.widget, forms.Textarea) else INPUT_CLASSES
            field.widget.attrs["class"] = css


class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ["cover_letter", "resume"]
        widgets = {
            "cover_letter": forms.Textarea(
                attrs={
                    "rows": 8,
                    "placeholder": "Tell us about yourself and why you'd be a great fit for this role...",
                },
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cover_letter"].required = False
        self.fields["cover_letter"].widget.attrs["class"] = TEXTAREA_CLASSES
        self.fields["resume"].widget.attrs["class"] = FILE_CLASSES
        self.fields["resume"].widget.attrs["accept"] = ".pdf,.doc,.docx"
