# lenders/urls.py
from django.urls import path
from .views import check_balance

urlpatterns = [
    path("check_balance/", check_balance, name="check_balance"),
]
