"""
User and profile models.

Design notes:
- Email is the username. The `username` field is gone entirely (cleaner than
  setting USERNAME_FIELD='email' but keeping username around).
- `role` is a TextChoices on User itself. We could've made it a separate
  Group, but keeping it as a field makes views/templates trivial and matches
  the brief.
- Profiles are OneToOne. We do NOT auto-create them with a signal. Profiles
  are created explicitly during registration based on the chosen role.
  Signals that auto-create profiles fight you forever when seeding data.
"""
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user with email login and a role field."""

    class Role(models.TextChoices):
        JOB_SEEKER = "job_seeker", "Job Seeker"
        EMPLOYER = "employer", "Employer"
        ADMIN = "admin", "Admin"

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=60, blank=True)
    last_name = models.CharField(max_length=60, blank=True)
    phone = models.CharField(max_length=20, blank=True)

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.JOB_SEEKER,
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []  # email + password are enough

    class Meta:
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        return self.email

    def get_full_name(self) -> str:
        full = f"{self.first_name} {self.last_name}".strip()
        return full or self.email

    def get_short_name(self) -> str:
        return self.first_name or self.email

    @property
    def is_job_seeker(self) -> bool:
        return self.role == self.Role.JOB_SEEKER

    @property
    def is_employer(self) -> bool:
        return self.role == self.Role.EMPLOYER

    @property
    def is_admin_role(self) -> bool:
        # `is_admin` collides with PermissionsMixin internals on some Django
        # versions, so we prefix it.
        return self.role == self.Role.ADMIN


class EmployerProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="employer_profile",
    )
    company_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["company_name"]

    def __str__(self) -> str:
        return self.company_name


class JobSeekerProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="job_seeker_profile",
    )
    bio = models.TextField(blank=True)
    # Comma-separated for now. Promote to a tags table later if needed.
    skills = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user.get_full_name()} (Job Seeker)"
