from django.contrib import admin, messages
from django.urls import path
from .models import Payment
from django.template.response import TemplateResponse
from .models import Lender, Loan, Payment, Booking, Apartment, SeasonalRate
from .forms import BookingAdminForm, LenderAdminForm
from django.utils.safestring import mark_safe
from decimal import Decimal
from .models import SentConfirmation
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from .signals import send_booking_confirmation, send_payment_confirmation
from django.http import HttpResponseRedirect

# 📆 Saisonpreise im Admin
@admin.register(SeasonalRate)
class SeasonalRateAdmin(admin.ModelAdmin):
    list_display = ("apartment", "start_date", "end_date", "percentage_adjustment")
    list_filter = ("apartment",)
    ordering = ("apartment__name", "start_date")


@admin.register(Lender)
class LenderAdmin(admin.ModelAdmin):
    form = LenderAdminForm

    list_display = (
        "first_name", "last_name", "email", "language",
        "discount_percent", "get_current_balance_display",
    )

    fieldsets = (
        (None, {
            'fields': ('first_name', 'last_name', 'email', 'language')
        }),
        ('Optional', {
            'classes': ('collapse',),
            'fields': ('mobile', 'whatsapp', 'postal_code', 'country', 'address', 'discount_percent')
        }),
    )

    def get_current_balance_display(self, obj):
        try:
            return f"{obj.current_balance():.2f} €"
        except Exception as e:
            return f"Fehler: {e}"

    get_current_balance_display.short_description = "Saldo"


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("lender", "date", "original_amount", "currency", "is_fixed_display", "get_amount_eur_display")
    list_filter = ("currency", "is_fixed", "date")
    search_fields = ("lender__first_name", "lender__last_name")

    @admin.display(description="Typ", ordering="is_fixed")
    def is_fixed_display(self, obj):
        return dict(obj.PAYMENT_TYPE_CHOICES).get(obj.is_fixed, "❓")
    def is_fixed_display(self, obj):
        return _("Fixbetrag") if obj.is_fixed else _("Flexibel")
    def get_amount_eur_display(self, obj):
        try:
            return f"{obj.amount_eur():,.2f} €"
        except Exception:
            return "–"

    get_amount_eur_display.short_description = "Betrag in EUR"


@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "price_per_night", "current_price_display", "is_active", "get_color_preview")

    def current_price_display(self, obj):
        return f"{obj.current_price():.2f} €"

    current_price_display.short_description = "Aktueller Preis"
    def get_color_preview(self, obj):
        return mark_safe(f"<div style='width: 30px; height: 20px; background:{obj.color}; border-radius: 4px;'>&nbsp;</div>")

    get_color_preview.short_description = "Farbe"


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    form = BookingAdminForm
    list_display = ("lender", "apartment", "start_date", "end_date", "total_cost_display", "custom_total_price")
    readonly_fields = ("_saldo_warnung",)

    fieldsets = (
        (None, {
            'fields': (
                '_saldo_warnung',
                'lender',
                'apartment',
                'start_date',
                'end_date',
                'custom_total_price',
                'override_confirm',
            )
        }),
    )

    def _saldo_warnung(self, obj):
        form = getattr(obj, 'form', None)
        if form and hasattr(form, 'warning_html'):
            return mark_safe(form.warning_html)
        return mark_safe('<div id="saldo-warning"></div>')

    _saldo_warnung.short_description = "⚠️ Warnung"

    def total_cost_display(self, obj):
        try:
            return f"{obj.total_cost():.2f} €"
        except Exception:
            return "–"

    total_cost_display.short_description = "Abgewohnter Betrag"

    class Media:
        js = ("lenders/js/check_balance.js",)

class CustomAdminSite(admin.AdminSite):
    site_header = "CBV Goodwill Admin"
    site_title = "CBV Admin"
    index_title = "Auswahlbereich"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("auswahlbereich/reports/raw/", self.admin_view(self.payment_list_raw), name="payment_list_raw"),
            path("auswahlbereich/reports/with-usage/", self.admin_view(self.payment_list_with_usage), name="payment_list_with_usage"),
            path("auswahlbereich/reports/apartments/", self.admin_view(self.apartment_price_list), name="apartment_price_list"),
        ]
        return custom_urls + urls

    def payment_list_raw(self, request):
        payments = Payment.objects.select_related("lender").order_by("lender__last_name", "date")
        return TemplateResponse(request, "admin/lenders/reports/payment_list_raw.html", {"payments": payments})

    def payment_list_with_usage(self, request):
        lenders = []
        for lender in Lender.objects.all():
            total_payments = sum(p.amount_eur() for p in lender.payments.all())
            total_used = sum(b.total_cost() for b in lender.bookings.all())
            balance = total_payments - total_used
            lenders.append({
                "name": lender,
                "total_payments": total_payments,
                "total_used": total_used,
                "balance": balance
            })
        return TemplateResponse(request, "admin/lenders/reports/payment_list_with_usage.html", {"lenders": lenders})

    def apartment_price_list(self, request):
        apartments = Apartment.objects.prefetch_related("seasonal_rates").all()
        return TemplateResponse(request, "admin/lenders/reports/apartment_price_list.html", {"apartments": apartments})

@admin.register(SentConfirmation)
class SentConfirmationAdmin(admin.ModelAdmin):
    list_display = ["sent_at", "lender", "linked_confirmation", "recipient", "language", "current_balance", "resend_button"]
    list_filter = ["language", "sent_at"]
    search_fields = ["lender__first_name", "lender__last_name", "recipient"]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("resend/<int:pk>/", self.admin_site.admin_view(self.resend_confirmation), name="lenders_resend_confirmation"),
        ]
        return custom_urls + urls

    @admin.display(description="Bestätigung")
    def linked_confirmation(self, obj):
        if obj.payment:
            url = reverse("admin:lenders_payment_change", args=[obj.payment.pk])
            return format_html("💰 <a href='{}'>Zahlung #{}</a>", url, obj.payment.pk)
        elif hasattr(obj, "booking") and obj.booking:
            url = reverse("admin:lenders_booking_change", args=[obj.booking.pk])
            return format_html("📅 <a href='{}'>Buchung #{}</a>", url, obj.booking.pk)
        return "—"

    @admin.display(description="Saldo")
    def current_balance(self, obj):
        return f"{obj.lender.current_balance():.2f} €"

    @admin.display(description="📧 Wieder senden")
    def resend_button(self, obj):
        url = reverse("admin:lenders_resend_confirmation", args=[obj.pk])
        return format_html(
            "<a class='button' style='padding: 4px 10px; background: #3e8ed0; color: white; border-radius: 4px; text-decoration: none;' href='{}'>Senden</a>", url
        )

    def resend_confirmation(self, request, pk):
        obj = SentConfirmation.objects.get(pk=pk)
        if obj.payment:
            send_payment_confirmation(sender=None, instance=obj.payment, created=False)
            msg = _("Zahlungsbestätigung wurde erneut gesendet.")
        elif hasattr(obj, "booking") and obj.booking:
            send_booking_confirmation(sender=None, instance=obj.booking, created=False)
            msg = _("Buchungsbestätigung wurde erneut gesendet.")
        else:
            msg = _("Keine zugehörige Buchung oder Zahlung gefunden.")

        self.message_user(request, msg, messages.SUCCESS)
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/admin/"))
                            
# Initialisiere neue AdminSite
custom_admin_site = CustomAdminSite(name="custom_admin")

# Registriere deine normalen Modelle dort
custom_admin_site.register(Lender)
custom_admin_site.register(Payment)
custom_admin_site.register(Apartment)

# 🗭 Link zur Kalenderansicht
admin.site.site_url = "/lenders/calendar/"
