"""
Job views: public list/detail/apply, employer post + dashboard, seeker dashboard.

Access rules:
- List + Detail: public.
- Apply: requires login + role=job_seeker. Duplicate prevention.
- Post + EmployerDashboard: requires login + role=employer.
- SeekerDashboard: requires login + role=job_seeker.

We use UserPassesTestMixin instead of a custom decorator. Less code, less magic,
plays nicely with Django's mixins.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import JobApplicationForm, JobPostingForm
from .models import JobApplication, JobPosting


class JobListView(ListView):
    """Public list of published jobs."""

    template_name = "jobs/list.html"
    context_object_name = "jobs"
    paginate_by = 20

    def get_queryset(self):
        qs = (
            JobPosting.objects
            .filter(status=JobPosting.Status.PUBLISHED)
            .select_related("employer", "employer__employer_profile")
        )
        # Basic text filter via ?q=
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(title__icontains=q) | qs.filter(location__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["query"] = self.request.GET.get("q", "")
        return ctx


class JobDetailView(DetailView):
    """Public job detail. Tells job seekers if they've already applied."""

    template_name = "jobs/detail.html"
    context_object_name = "job"

    def get_queryset(self):
        return (
            JobPosting.objects
            .filter(status=JobPosting.Status.PUBLISHED)
            .select_related("employer", "employer__employer_profile")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated and getattr(user, "is_job_seeker", False):
            ctx["has_applied"] = JobApplication.objects.filter(
                job=self.object, applicant=user
            ).exists()
        return ctx


class JobApplyView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Job seekers apply to a specific job."""

    form_class = JobApplicationForm
    template_name = "jobs/apply.html"

    def test_func(self):
        return getattr(self.request.user, "is_job_seeker", False)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.warning(
                self.request,
                "Only job seekers can apply to jobs. Switch accounts to continue.",
            )
            return redirect("home")
        return super().handle_no_permission()

    def dispatch(self, request, *args, **kwargs):
        self.job = get_object_or_404(
            JobPosting,
            pk=kwargs["pk"],
            status=JobPosting.Status.PUBLISHED,
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["job"] = self.job
        return ctx

    def form_valid(self, form):
        # Friendly message for duplicates instead of relying on the DB constraint to 500.
        if JobApplication.objects.filter(job=self.job, applicant=self.request.user).exists():
            messages.warning(self.request, "You've already applied to this job.")
            return redirect("jobs:detail", pk=self.job.pk)
        form.instance.job = self.job
        form.instance.applicant = self.request.user
        response = super().form_valid(form)
        # Fire off notifications. Wrapped in try/except as defense in depth so
        # a SendGrid hiccup never breaks the user flow — the application is
        # already saved by this point, we just can't tell people about it.
        try:
            from .emails import send_application_confirmation, send_application_to_employer
            send_application_to_employer(self.object)
            send_application_confirmation(self.object)
        except Exception:
            import logging
            logging.getLogger(__name__).exception(
                "Email notifications failed for application %s; application is saved.",
                self.object.pk,
            )
        messages.success(
            self.request,
            f"Application submitted for {self.job.title}. Good luck!",
        )
        return response

    def get_success_url(self):
        return reverse("jobs:seeker_dashboard")


class JobPostView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Employers create a new job posting."""

    form_class = JobPostingForm
    template_name = "jobs/post.html"
    success_url = reverse_lazy("jobs:employer_dashboard")

    def test_func(self):
        return getattr(self.request.user, "is_employer", False)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.warning(
                self.request,
                "Only employers can post jobs.",
            )
            return redirect("home")
        return super().handle_no_permission()

    def form_valid(self, form):
        form.instance.employer = self.request.user
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"'{self.object.title}' is live.",
        )
        return response


class EmployerDashboardView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Employer sees their own jobs and application counts."""

    template_name = "jobs/employer_dashboard.html"
    context_object_name = "jobs"

    def test_func(self):
        return getattr(self.request.user, "is_employer", False)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return redirect("home")
        return super().handle_no_permission()

    def get_queryset(self):
        return (
            JobPosting.objects
            .filter(employer=self.request.user)
            .prefetch_related("applications")
        )


class SeekerDashboardView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Job seeker sees their applications."""

    template_name = "jobs/seeker_dashboard.html"
    context_object_name = "applications"

    def test_func(self):
        return getattr(self.request.user, "is_job_seeker", False)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return redirect("home")
        return super().handle_no_permission()

    def get_queryset(self):
        return (
            JobApplication.objects
            .filter(applicant=self.request.user)
            .select_related("job", "job__employer")
        )


class JobApplicationsView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Employer-facing: view all applications for one of their jobs.
    Resume links, cover letters, applicant email, and an inline status form
    all live here so the employer manages everything from one screen.
    """

    template_name = "jobs/job_applications.html"
    context_object_name = "applications"
    paginate_by = 25

    def test_func(self):
        return getattr(self.request.user, "is_employer", False)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return redirect("home")
        return super().handle_no_permission()

    def get_job(self):
        # Cached so we don't re-query in get_queryset and get_context_data.
        if not hasattr(self, "_job"):
            self._job = get_object_or_404(
                JobPosting,
                pk=self.kwargs["pk"],
                employer=self.request.user,
            )
        return self._job

    def get_queryset(self):
        return (
            JobApplication.objects
            .filter(job=self.get_job())
            .select_related("applicant")
            .order_by("-applied_at")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["job"] = self.get_job()
        ctx["status_choices"] = JobApplication.Status.choices
        return ctx


class ApplicationStatusUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    POST-only endpoint to change an application's status from the applications
    page. Ownership enforced via the queryset filter on employer.
    """

    model = JobApplication
    fields = ["status"]
    http_method_names = ["post"]

    def test_func(self):
        return getattr(self.request.user, "is_employer", False)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return redirect("home")
        return super().handle_no_permission()

    def get_queryset(self):
        # An employer can only mutate applications to jobs they own.
        return JobApplication.objects.filter(job__employer=self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        applicant_label = (
            self.object.applicant.get_full_name() or self.object.applicant.email
        )
        messages.success(
            self.request,
            f"{applicant_label}'s application marked as {self.object.get_status_display()}.",
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Invalid status value.")
        return redirect("jobs:job_applications", pk=self.object.job.pk)

    def get_success_url(self):
        return reverse("jobs:job_applications", kwargs={"pk": self.object.job.pk})
