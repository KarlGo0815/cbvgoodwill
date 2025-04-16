from django.urls import path
from . import views

urlpatterns = [
    path("check_balance/", views.check_balance, name="check_balance"),
    path("calendar/", views.calendar_view, name="calendar_view"),
    path("calendar/events/", views.booking_events, name="booking_events"),
]