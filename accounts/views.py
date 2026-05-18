"""
Authentication views.

Login and logout use Django's built-in views from accounts/urls.py — only
registration needs custom logic (because of the multi-step User + Profile
creation and the auto-login-on-success UX).
"""
from django.contrib import messages
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import RegistrationForm


class RegisterView(CreateView):
    form_class = RegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        response = super().form_valid(form)
        # Log the user in immediately so they don't have to log in after signing up.
        login(self.request, self.object)
        messages.success(
            self.request,
            f"Welcome, {self.object.get_short_name()}! Your account is ready.",
        )
        return response
