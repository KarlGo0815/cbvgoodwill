from django.urls import path
from . import views

urlpatterns = [
    path("calendar/", views.calendar_view, name="calendar"),
    path("calendar/events/", views.booking_events, name="booking_events"),
    path("check_booking_warnings/", views.check_booking_warnings, name="check_booking_warnings"),
    path("check_balance/", views.check_balance, name="check_balance"),

    # 📄 Admin Reports
    path("reports/raw/", views.payment_list_raw, name="payment_list_raw"),
    path("reports/with-usage/", views.payment_list_with_usage, name="payment_list_with_usage"),
    path("reports/apartments/", views.apartment_price_list, name="apartment_price_list"),
]
