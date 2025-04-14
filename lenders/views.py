# lenders/views.py
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from .models import Lender, Apartment
from datetime import datetime

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

        lender = Lender.objects.get(id=lender_id)
        apartment = Apartment.objects.get(id=apartment_id)

        start = datetime.strptime(start, "%Y-%m-%d").date()
        end = datetime.strptime(end, "%Y-%m-%d").date()
        nights = (end - start).days

        if nights <= 0:
            return JsonResponse({"status": "invalid_dates"})

        rabatt = lender.discount_percent or 0
        preis = apartment.price_per_night
        kosten = round(nights * preis * (1 - rabatt / 100), 2)
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
