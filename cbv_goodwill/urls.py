from django.contrib import admin
from django.urls import path, include
from lenders.admin import custom_admin_site  # 👈 deine eigene AdminSite

urlpatterns = [
    path("admin/", custom_admin_site.urls),  # 👈 wichtig!
    path("lenders/", include("lenders.urls")),
]
