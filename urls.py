from django.contrib import admin
from django.urls import path, include
from lenders.admin import custom_admin_site

urlpatterns = [
    path("admin/", custom_admin_site.urls),  # ← deine eigene AdminSite
    path("lenders/", include("lenders.urls")),  # ← App-URLs
]
