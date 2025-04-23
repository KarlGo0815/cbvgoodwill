# cbv_goodwill/urls.py
from lenders.admin import custom_admin_site
from django.shortcuts import render
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def landing(request):
    return render(request, "landing.html")
urlpatterns = [
    path("admin/", custom_admin_site.urls),
    path("lenders/", include("lenders.urls")),
    path("", landing),  # Saubere Landing Page auf Root
]