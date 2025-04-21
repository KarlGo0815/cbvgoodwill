from django.contrib import admin
from django.urls import path
from django.template.response import TemplateResponse
from .models import Lender, Loan, Payment, Booking, Apartment, SeasonalRate
from .forms import BookingAdminForm, LenderAdminForm
from django.utils.safestring import mark_safe
from decimal import Decimal
from .models import SentConfirmation

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
    list_display = ("lender", "date", "original_amount", "currency", "get_amount_eur_display")
    list_filter = ("currency", "date")
    search_fields = ("lender__first_name", "lender__last_name")

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
    list_display = ("sent_at", "lender", "payment", "language", "recipient")
    list_filter = ("language", "sent_at")
    search_fields = ("lender__first_name", "lender__last_name", "recipient")
    ordering = ("-sent_at",)
    
# Initialisiere neue AdminSite
custom_admin_site = CustomAdminSite(name="custom_admin")

# Registriere deine normalen Modelle dort
custom_admin_site.register(Lender)
custom_admin_site.register(Payment)
custom_admin_site.register(Apartment)

# 🗭 Link zur Kalenderansicht
admin.site.site_url = "/lenders/calendar/"
