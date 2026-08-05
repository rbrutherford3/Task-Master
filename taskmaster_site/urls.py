from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # To serve Task Master under /taskmaster/ instead of the site root,
    # change the line below from path("", include("taskmaster.urls"))
    # to path("taskmaster/", include("taskmaster.urls")).
    path("", include("taskmaster.urls")),
]
