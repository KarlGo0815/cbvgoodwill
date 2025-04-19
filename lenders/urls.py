from django.urls import path
from . import views

urlpatterns = [
    path("calendar/", views.calendar_view, name="calendar"),
    path("calendar/events/", views.booking_events, name="calendar_events"),  # 👉 hinzufügen!
    path("check_booking_warnings/", views.check_booking_warnings, name="check_booking_warnings"),
    path("check_balance/", views.check_balance, name="check_balance"),  # ggf. alt
]
