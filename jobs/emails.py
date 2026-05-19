"""
Transactional emails for the jobs app.

These are called from JobApplyView. fail_silently=True so a SendGrid hiccup
never breaks the user flow — the application is already saved by the time
we get here, we just can't tell people about it.
"""
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse

logger = logging.getLogger(__name__)


def _absolute(path: str) -> str:
    """Build an absolute URL for the current environment."""
    base = settings.SITE_BASE_URL.rstrip("/")
    return base + path


def _send(subject: str, to: list[str], template_base: str, context: dict) -> None:
    """Shared sender. template_base is 'emails/foo' (no extension)."""
    text_body = render_to_string(f"{template_base}.txt", context)
    html_body = render_to_string(f"{template_base}.html", context)
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=to,
    )
    msg.attach_alternative(html_body, "text/html")
    try:
        msg.send(fail_silently=False)
    except Exception as e:
        # Log but don't blow up the request.
        logger.exception("Failed to send email '%s' to %s: %s", subject, to, e)


def send_application_to_employer(application) -> None:
    job = application.job
    employer = job.employer
    context = {
        "job": job,
        "applicant": application.applicant,
        "application": application,
        "dashboard_url": _absolute(reverse("jobs:job_applications", args=[job.pk])),
    }
    _send(
        subject=f"New application: {job.title}",
        to=[employer.email],
        template_base="emails/application_to_employer",
        context=context,
    )


def send_application_confirmation(application) -> None:
    job = application.job
    applicant = application.applicant
    context = {
        "job": job,
        "applicant": applicant,
        "job_url": _absolute(reverse("jobs:detail", args=[job.pk])),
        "dashboard_url": _absolute(reverse("jobs:seeker_dashboard")),
    }
    _send(
        subject=f"Application received: {job.title}",
        to=[applicant.email],
        template_base="emails/application_confirmation",
        context=context,
    )
