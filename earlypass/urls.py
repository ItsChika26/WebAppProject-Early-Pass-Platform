from django.contrib import admin
from django.urls import path, include
from passes import views as pv

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", pv.home, name="home"),
    path("classes/", include(("passes.urls_classes", "classes"))),
    path("submissions/", include(("passes.urls_submissions", "submissions"))),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
