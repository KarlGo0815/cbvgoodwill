from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("lenders/", include("lenders.urls")),  # ✅ das hier ist wichtig
]
