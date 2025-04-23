from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from .models import Lender, Apartment, Booking
from datetime import datetime, timedelta
from decimal import Decimal

# -------------------------------
# 📅 Kalenderansicht
# -------------------------------

def lenders_home(request):
    return HttpResponse("Willkommen im Lenders-Bereich!")
    
@staff_member_required
def calendar_view(request):
    from .models import Apartment, Booking
    from datetime import timedelta

    apartments = Apartment.objects.all()
    bookings = Booking.objects.select_related("apartment", "lender").all()

    events = []
    for booking in bookings:
        color = booking.apartment.color or "#999999"
        events.append({
            "title": f"{booking.apartment.name} – {booking.lender.first_name}",
            "start": booking.start_date.isoformat(),
            "end": (booking.end_date + timedelta(days=1)).isoformat(),
            "color": color,
        })

    return render(request, "lenders/calendar.html", {
        "bookings": events,  # <-- das brauchst du
        "apartments": apartments,
    })

@staff_member_required
def booking_events(request):
    """Liefert alle Buchungen als JSON (für FullCalendar oder JS-Frontend)."""
    def get_contrast_color(hex_color):
        hex_color = hex_color.lstrip('#')
        r, g, b = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
        brightness = (r*299 + g*587 + b*114) / 1000
        return '#000000' if brightness > 150 else '#ffffff'

    bookings = Booking.objects.select_related("apartment", "lender").all()
    events = []

    for booking in bookings:
        color = booking.apartment.color or "#999999"
        text_color = get_contrast_color(color)

        events.append({
            "title": f"{booking.apartment.name} – {booking.lender.first_name}",
            "start": booking.start_date.isoformat(),
            "end": (booking.end_date + timedelta(days=1)).isoformat(),
            "color": color,
            "textColor": text_color,
        })

    return JsonResponse(events, safe=False)


# -------------------------------
# ✅ Neue kombinierte Prüfung
# -------------------------------

@csrf_exempt
@staff_member_required
def check_booking_warnings(request):
    """Prüft Saldo und Villa-Blockierung."""
    apartment_id = request.POST.get("apartment")
    lender_id = request.POST.get("lender")
    start = request.POST.get("start_date")
    end = request.POST.get("end_date")

    if not all([apartment_id, lender_id, start, end]):
        return JsonResponse({"status": "incomplete"})

    apartment = Apartment.objects.get(id=apartment_id)
    lender = Lender.objects.get(id=lender_id)
    start = datetime.strptime(start, "%Y-%m-%d").date()
    end = datetime.strptime(end, "%Y-%m-%d").date()
    nights = (end - start).days

    warnings = []

    rabatt = lender.discount_percent or Decimal('0')
    preis = apartment.price_per_night
    kosten = (Decimal(nights) * preis * (Decimal('1') - rabatt / Decimal('100'))).quantize(Decimal('0.01'))
    saldo = lender.current_balance()

    if kosten > saldo:
        warnings.append(
            f"⚠️ Guthaben: Buchung kostet <strong>{kosten:.2f} €</strong>, Guthaben beträgt nur <strong>{saldo:.2f} €</strong>."
        )

    if apartment.name.strip().lower() == "la villa complete":
        other_apartments = Apartment.objects.exclude(name__iexact="La Villa Complete")
        all_occupied = True
        for apt in other_apartments:
            if not Booking.objects.filter(
                apartment=apt,
                start_date__lt=end,
                end_date__gt=start,
            ).exists():
                all_occupied = False
                break

        if all_occupied:
            warnings.append(
                "📌 Hinweis: 'La Villa Complete' darf nur gebucht werden, wenn <strong>mindestens eine andere Wohnung frei</strong> ist."
            )

    return JsonResponse({"status": "ok", "warnings": warnings})


# -------------------------------
# 🧪 Fallback (alte API für check_balance.js)
# -------------------------------

@csrf_exempt
@staff_member_required
def check_balance(request):
    """Nur Saldo-Prüfung – Legacy-Kompatibilität für JS."""
    lender_id = request.POST.get("lender")
    apartment_id = request.POST.get("apartment")
    start = request.POST.get("start_date")
    end = request.POST.get("end_date")

    if not all([lender_id, apartment_id, start, end]):
        return JsonResponse({"status": "incomplete"})

    lender = Lender.objects.get(id=lender_id)
    apartment = Apartment.objects.get(id=apartment_id)

    start = datetime.strptime(start, "%Y-%m-%d").date()
    end = datetime.strptime(end, "%Y-%m-%d").date()
    nights = (end - start).days

    if nights <= 0:
        return JsonResponse({"status": "invalid_dates"})

    rabatt = lender.discount_percent or Decimal('0')
    preis = apartment.price_per_night
    kosten = (Decimal(nights) * preis * (Decimal('1') - rabatt / Decimal('100'))).quantize(Decimal('0.01'))
    saldo = lender.current_balance()

    if kosten > saldo:
        return JsonResponse({
            "status": "warning",
            "saldo": f"{saldo:.2f}",
            "kosten": f"{kosten:.2f}"
        })
    else:
        return JsonResponse({"status": "ok"})
        
  # -------------------------------
# 📄 Admin-Reports
# -------------------------------
from .models import Payment  # Stelle sicher, dass Payment importiert ist
from collections import defaultdict

@staff_member_required
def payment_list_raw(request):
    """Alle Zahlungen, sortiert nach Lender und Datum."""
    payments = Payment.objects.select_related("lender").order_by("lender__last_name", "date")
    return render(request, "admin/lenders/reports/payment_list_raw.html", {
        "payments": payments
    })


@staff_member_required
def payment_list_with_usage(request):
    """Zahlungen mit Aufstellung der verbrauchten Buchungskosten."""
    lender_data = defaultdict(lambda: {"payments": [], "total": Decimal(0), "used": Decimal(0)})

    for payment in Payment.objects.select_related("lender").all():
        data = lender_data[payment.lender]
        data["payments"].append(payment)
        data["total"] += payment.amount_eur()

    for booking in Booking.objects.select_related("lender").all():
        lender_data[booking.lender]["used"] += booking.total_cost()

    return render(request, "admin/lenders/reports/payment_list_with_usage.html", {
        "lender_data": dict(lender_data)
    })


@staff_member_required
def apartment_price_list(request):
    """Schöne Preisliste für Appartements."""
    apartments = Apartment.objects.filter(is_active=True).order_by("name")
    return render(request, "admin/lenders/reports/apartment_price_list.html", {
        "apartments": apartments
    })
      
from django.shortcuts import render

def lenders_home(request):
    return render(request, "lenders/home.html")
