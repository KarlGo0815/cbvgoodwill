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
    events = [
        {
            "title": f"{booking.apartment.name} – {booking.lender.first_name}",
            "start": booking.start_date.isoformat(),
            "end": (booking.end_date + timedelta(days=1)).isoformat(),
            "color": "#ff6666",
        }
        for booking in bookings
    ]

    return JsonResponse(events, safe=False)

# -------------------------------
# ⚠️ Guthabenprüfung bei Buchung
# -------------------------------

@csrf_exempt
@staff_member_required
def check_balance(request):
    try:
        lender_id = request.POST.get("lender")
        apartment_id = request.POST.get("apartment")
        start = request.POST.get("start_date")
        end = request.POST.get("end_date")

        if not all([lender_id, apartment_id, start, end]):
            return JsonResponse({"status": "incomplete"})

        lender = get_object_or_404(Lender, id=lender_id)
        apartment = get_object_or_404(Apartment, id=apartment_id)

        start_date = datetime.strptime(start, "%Y-%m-%d").date()
        end_date = datetime.strptime(end, "%Y-%m-%d").date()
        nights = (end_date - start_date).days

        if nights <= 0:
            return JsonResponse({"status": "invalid_dates"})

        rabatt = lender.discount_percent or Decimal('0.0')
        preis = apartment.price_per_night

        kosten = (Decimal(nights) * preis * (Decimal('1.0') - rabatt / Decimal('100.0'))).quantize(Decimal('0.01'))
        saldo = lender.current_balance()

        if kosten > saldo:
            return JsonResponse({
                "status": "warning",
                "saldo": f"{saldo:.2f}",
                "kosten": f"{kosten:.2f}"
            })
        else:
            return JsonResponse({"status": "ok"})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})
