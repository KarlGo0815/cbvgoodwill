from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Lender, Loan, Payment, Booking, Apartment
from .forms import BookingAdminForm

@admin.register(Lender)
class LenderAdmin(admin.ModelAdmin):
    list_display = (
        "first_name", "last_name", "email", "language",
        "discount_percent", "current_balance_display",
    )

    def current_balance_display(self, obj):
        try:
            return f"{obj.current_balance():.2f} €"
        except Exception as e:
            return f"Fehler: {e}"
    current_balance_display.short_description = "Saldo"


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("lender", "date", "original_amount", "currency", "amount_eur_display")
    list_filter = ("currency", "date")
    search_fields = ("lender__first_name", "lender__last_name")

    def amount_eur_display(self, obj):
        try:
            return f"{obj.amount_eur():,.2f} €"
        except Exception:
            return "–"
    amount_eur_display.short_description = "Betrag in EUR"


@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "price_per_night", "is_active")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    form = BookingAdminForm
    list_display = ("lender", "apartment", "start_date", "end_date", "total_cost_display")
    readonly_fields = ("_saldo_warnung",)

    fieldsets = (
        (None, {
            'fields': (
                '_saldo_warnung',
                'lender',
                'apartment',
                'start_date',
                'end_date',
            )
        }),
    )

    def _saldo_warnung(self, obj):
        # Div für JavaScript-Warnung
        return mark_safe('<div id="saldo-warning"></div>')

    _saldo_warnung.short_description = "Guthabenprüfung"

    def total_cost_display(self, obj):
        try:
            return f"{obj.total_cost():.2f} €"
        except Exception:
            return "–"
    total_cost_display.short_description = "Abgewohnter Betrag"

    class Media:
        js = ("lenders/js/check_balance.js",)  # <-- dein JS wird hier eingebunden
