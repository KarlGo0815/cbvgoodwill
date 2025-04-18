from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Lender, Loan, Payment, Booking, Apartment, SeasonalRate
from .forms import BookingAdminForm, LenderAdminForm


# 📆 Saisonpreise im Admin
@admin.register(SeasonalRate)
class SeasonalRateAdmin(admin.ModelAdmin):
    list_display = ("apartment", "start_date", "end_date", "price_per_night")
    list_filter = ("apartment",)
    search_fields = ("apartment__name",)
    ordering = ("apartment__name", "start_date")  # Gruppiert nach Apartment, sortiert nach Startdatum


@admin.register(Lender)
class LenderAdmin(admin.ModelAdmin):
    form = LenderAdminForm

    list_display = (
        "first_name", "last_name", "email", "language",
        "discount_percent", "current_balance_display",
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
    list_display = ("name", "price_per_night", "is_active", "color_preview")
    readonly_fields = ("color_preview",)
    fields = ("name", "description", "price_per_night", "is_active", "color", "color_preview")

    def color_preview(self, obj):
        return mark_safe(f'<div style="width: 30px; height: 20px; background: {obj.color}; border: 1px solid #999;"></div>')
    color_preview.short_description = "Vorschau"


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
        """Dieses Feld zeigt Warnungen im Admin-Formular an."""
        warning_html = ""
        try:
            form = getattr(obj, 'form', None)
            if form and hasattr(form, 'warning_html'):
                warning_html = form.warning_html
        except Exception:
            pass

        # Immer das Div anzeigen, damit JS es finden kann
        return mark_safe(f'<div id="saldo-warning">{warning_html}</div>')

    _saldo_warnung.short_description = "⚠️ Warnung"

    def total_cost_display(self, obj):
        try:
            return f"{obj.total_cost():.2f} €"
        except Exception:
            return "–"

    total_cost_display.short_description = "Abgewohnter Betrag"

    class Media:
        js = ("lenders/js/check_balance.js",)  # Dein JS zur Live-Guthabenprüfung

# 📍 Link im Admin zur Kalenderansicht
admin.site.site_url = "/lenders/calendar/"
