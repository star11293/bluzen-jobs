"""
Job posting and application models.
"""
from django.conf import settings
from django.db import models
from django.urls import reverse


class JobPosting(models.Model):
    class JobType(models.TextChoices):
        FULL_TIME = "full_time", "Full-time"
        PART_TIME = "part_time", "Part-time"
        PER_DIEM = "per_diem", "Per Diem"
        CONTRACT = "contract", "Contract"
        TEMPORARY = "temporary", "Temporary"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        CLOSED = "closed", "Closed"

    employer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_postings",
        limit_choices_to={"role": "employer"},
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200)
    job_type = models.CharField(max_length=20, choices=JobType.choices, default=JobType.FULL_TIME)
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PUBLISHED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "-created_at"])]

    def __str__(self) -> str:
        return f"{self.title} ({self.location})"

    def get_absolute_url(self) -> str:
        return reverse("jobs:detail", args=[self.pk])


class JobApplication(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"

    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications",
        limit_choices_to={"role": "job_seeker"},
    )
    cover_letter = models.TextField(blank=True)
    resume = models.FileField(upload_to="resumes/%Y/%m/")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["job", "applicant"], name="unique_job_applicant")]
