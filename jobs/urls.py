from django.urls import path

from .views import (
    ApplicationStatusUpdateView,
    EmployerDashboardView,
    JobApplicationsView,
    JobApplyView,
    JobDetailView,
    JobListView,
    JobPostView,
    SeekerDashboardView,
)

app_name = "jobs"

urlpatterns = [
    path("jobs/", JobListView.as_view(), name="list"),
    path("jobs/post/", JobPostView.as_view(), name="post"),
    path("jobs/<int:pk>/", JobDetailView.as_view(), name="detail"),
    path("jobs/<int:pk>/apply/", JobApplyView.as_view(), name="apply"),
    path("jobs/<int:pk>/applications/", JobApplicationsView.as_view(), name="job_applications"),
    path("applications/<int:pk>/status/", ApplicationStatusUpdateView.as_view(), name="application_status"),
    path("dashboard/employer/", EmployerDashboardView.as_view(), name="employer_dashboard"),
    path("dashboard/applications/", SeekerDashboardView.as_view(), name="seeker_dashboard"),
]
