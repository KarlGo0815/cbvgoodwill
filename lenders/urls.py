from django.urls import path
from . import views

app_name = "lenders"  # optional, aber empfohlen für Namensräume

urlpatterns = [
    # 📆 Kalender-Ansicht
    path("calendar/", views.calendar_view, name="calendar"),
    path("calendar/events/", views.booking_events, name="booking_events"),

    # ⚠️ Ajax-Checks
    path("check_booking_warnings/", views.check_booking_warnings, name="check_booking_warnings"),
    path("check_balance/", views.check_balance, name="check_balance"),

    # 📄 Reports (z. B. über Menü "Auswahlbereich" oder direkt)
    path("reports/raw/", views.payment_list_raw, name="report_raw_payments"),
    path("reports/with-usage/", views.payment_list_with_usage, name="report_payments_with_usage"),
    path("reports/apartments/", views.apartment_price_list, name="report_apartment_prices"),
]
