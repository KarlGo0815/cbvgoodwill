from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from .models import Lender, Apartment, Booking
from datetime import datetime, timedelta
from decimal import Decimal

# -------------------------------
# 📅 Kalenderansicht
# -------------------------------

@staff_member_required
def calendar_view(request):
    """Rendert die Kalenderseite für Buchungen."""
    return render(request, 'calendar.html')


@staff_member_required
def booking_events(request):
    """Liefert alle Buchungen als JSON (für FullCalendar oder JS-Frontend)."""
    bookings = Booking.objects.select_related("apartment", "lender").all()
    events = []

    for booking in bookings:
        color = booking.apartment.color or "#999999"  # Fallback falls keine Farbe gesetzt
        events.append({
            "title": f"{booking.apartment.name} – {booking.lender.first_name}",
            "start": booking.start_date.isoformat(),
            "end": (booking.end_date + timedelta(days=1)).isoformat(),  # FullCalendar benötigt exclusive end
            "color": color,
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
