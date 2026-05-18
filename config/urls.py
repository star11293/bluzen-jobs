from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("", include("jobs.urls")),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# Friendlier admin labels for the built-in admin.
admin.site.site_header = "Bluzen Healthcare Staffing"
admin.site.site_title = "Bluzen Admin"
admin.site.index_title = "Administration"
