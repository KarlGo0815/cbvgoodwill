from django.contrib import admin, messages
from django import forms
from django.template.loader import render_to_string
from django.urls import path, reverse
from django.template.response import TemplateResponse
from django.http import HttpResponseRedirect
from django.utils.html import format_html, mark_safe, strip_tags
from django.utils.translation import gettext_lazy as _, activate
from django.core.mail import EmailMultiAlternatives
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group
from decimal import Decimal

from .models import (
    Lender, Loan, Payment, Booking, Apartment,
    SeasonalRate, SentConfirmation
)
from .forms import BookingAdminForm, LenderAdminForm
from .signals import send_booking_confirmation, send_payment_confirmation

# -----------------------
# 📧 Admin E-Mail-Formular
# -----------------------
class AdminEmailForm(forms.Form):
    lender = forms.ModelChoiceField(
        queryset=Lender.objects.all().order_by("last_name"),
        label="Lender auswählen (optional)",
        required=False
    )
    custom_email = forms.EmailField(label="Oder neue E-Mail-Adresse", required=False)
    language = forms.ChoiceField(label="Sprache", choices=[("de", "Deutsch"), ("en", "Englisch")])
    subject = forms.CharField(label="Betreff", max_length=200)
    message = forms.CharField(label="Nachricht", widget=forms.Textarea(attrs={"rows": 6}))

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("lender") and not cleaned_data.get("custom_email"):
            raise ValidationError("Bitte entweder einen Lender auswählen oder eine E-Mail-Adresse eingeben.")
        return cleaned_data

# -----------------------
# 📌 Custom AdminSite
# -----------------------
class CustomAdminSite(admin.AdminSite):
    site_header = "CBV Goodwill Admin"
    site_title = "CBV Admin"
    index_title = "Menue - Auswahlbereich"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("auswahlbereich/reports/raw/", self.admin_view(self.payment_list_raw), name="payment_list_raw"),
            path("auswahlbereich/reports/with-usage/", self.admin_view(self.payment_list_with_usage), name="payment_list_with_usage"),
            path("auswahlbereich/reports/apartments/", self.admin_view(self.apartment_price_list), name="apartment_price_list"),
            path("send-email/", self.admin_view(self.send_email_view), name="send_custom_email"),
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
                "lender": lender,
                "total_payments": total_payments,
                "total_used": total_used,
                "balance": balance
            })
        return TemplateResponse(
            request,
            "admin/lenders/reports/payment_list_with_usage.html",
            {"lenders": lenders}
        )

    def apartment_price_list(self, request):
        apartments = Apartment.objects.prefetch_related("seasonal_rates").all()
        return TemplateResponse(request, "admin/lenders/reports/apartment_price_list.html", {"apartments": apartments})

    def send_email_view(self, request):
        form = AdminEmailForm(request.POST or None)
        if request.method == "POST" and form.is_valid():
            lender = form.cleaned_data["lender"]
            custom_email = form.cleaned_data["custom_email"]
            language = form.cleaned_data["language"]
            subject = form.cleaned_data["subject"]
            message = form.cleaned_data["message"]

            recipient = custom_email or (lender.email if lender else None)

            if not lender and custom_email:
                lender = Lender.objects.create(
                    email=custom_email,
                    first_name="(neu)",
                    last_name="(manuell)",
                    address="",
                    postal_code="",
                    country="",
                    language=language
                )

            if recipient:
                activate(language)
                html_content = render_to_string("emails/custom_email.html", {
                    "message": message,
                    "subject": subject,
                    "language": language,
                    "recipient": recipient,
                })

                email = EmailMultiAlternatives(
                    subject,
                    strip_tags(html_content),
                    "Casa Bella Vista <casabelavista@amt-fuer-liebe-und-dankbarkeit.de>",
                    [recipient]
                )
                email.attach_alternative(html_content, "text/html")
                email.send()

                self.message_user(request, f"E-Mail erfolgreich an {recipient} gesendet ✅")
                return HttpResponseRedirect("/admin/")

        context = {
            **self.each_context(request),
            "title": "✉️ E-Mail senden",
            "form": form
        }
        return TemplateResponse(request, "admin/send_email_form.html", context)

# -----------------------
# 📌 Custom Admin Registrierungen
# -----------------------

custom_admin_site = CustomAdminSite(name="custom_admin")

@admin.register(Lender, site=custom_admin_site)
class LenderAdmin(admin.ModelAdmin):
    form = LenderAdminForm
    list_display = ("first_name", "last_name", "email", "language", "discount_percent", "get_current_balance_display")

    @admin.display(description="Saldo")
    def get_current_balance_display(self, obj):
        try:
            return f"{obj.current_balance():.2f} €"
        except Exception as e:
            return f"Fehler: {e}"

@admin.register(Payment, site=custom_admin_site)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("lender", "date", "original_amount", "currency", "is_fixed_display", "get_amount_eur_display")
    list_filter = ("currency", "is_fixed", "date")
    search_fields = ("lender__first_name", "lender__last_name")

    @admin.display(description="Typ")
    def is_fixed_display(self, obj):
        return _("Fixbetrag") if obj.is_fixed else _("Flexibel")

    @admin.display(description="Betrag in EUR")
    def get_amount_eur_display(self, obj):
        try:
            return f"{obj.amount_eur():,.2f} €"
        except Exception:
            return "–"

@admin.register(Apartment, site=custom_admin_site)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "price_per_night", "get_color_preview", "is_active")

    @admin.display(description="Farbe")
    def get_color_preview(self, obj):
        return mark_safe(f"<div style='width: 30px; height: 20px; background:{obj.color}; border-radius: 4px;'>&nbsp;</div>")

@admin.register(SeasonalRate, site=custom_admin_site)
class SeasonalRateAdmin(admin.ModelAdmin):
    list_display = ("apartment", "start_date", "end_date", "percentage_adjustment")
    list_filter = ("apartment",)
    ordering = ("apartment__name", "start_date")

@admin.register(Booking, site=custom_admin_site)
class BookingAdmin(admin.ModelAdmin):
    form = BookingAdminForm
    list_display = ("lender", "apartment", "start_date", "end_date", "total_cost_display", "custom_total_price")
    readonly_fields = ("_saldo_warnung",)

    @admin.display(description="⚠️ Warnung")
    def _saldo_warnung(self, obj):
        form = getattr(obj, 'form', None)
        if form and hasattr(form, 'warning_html'):
            return mark_safe(form.warning_html)
        return mark_safe('<div id="saldo-warning"></div>')

    @admin.display(description="Abgewohnter Betrag")
    def total_cost_display(self, obj):
        try:
            return f"{obj.total_cost():.2f} €"
        except Exception:
            return "–"

    class Media:
        js = ("lenders/js/check_balance.js",)

@admin.register(SentConfirmation, site=custom_admin_site)
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
        if obj.booking:
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
            "<a class='button' style='padding: 4px 10px; background: #3e8ed0; color: white; border-radius: 4px; text-decoration: none;' href='{}'>Senden</a>",
            url
        )

    def resend_confirmation(self, request, pk):
        obj = SentConfirmation.objects.get(pk=pk)
        if obj.payment:
            send_payment_confirmation(sender=None, instance=obj.payment, created=False)
            msg = _("Zahlungsbestätigung wurde erneut gesendet.")
        elif obj.booking:
            send_booking_confirmation(sender=None, instance=obj.booking, created=False)
            msg = _("Buchungsbestätigung wurde erneut gesendet.")
        else:
            msg = _("Keine zugehörige Buchung oder Zahlung gefunden.")
        self.message_user(request, msg, messages.SUCCESS)
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/admin/"))

# Auth
custom_admin_site.register(User)
custom_admin_site.register(Group)

# Kalender-Link
admin.site.site_url = "/lenders/calendar/"
