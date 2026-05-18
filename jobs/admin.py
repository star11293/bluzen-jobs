from django.contrib import admin
from .models import JobApplication, JobPosting


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ("title", "employer", "location", "status", "created_at")
    search_fields = ("title", "employer__email")
    autocomplete_fields = ("employer",)


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ("applicant", "job", "status", "applied_at")
    search_fields = ("applicant__email", "job__title")
    autocomplete_fields = ("job", "applicant")
