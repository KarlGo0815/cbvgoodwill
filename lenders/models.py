from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from datetime import date
from decimal import Decimal
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import activate, get_language
from django.conf import settings
from django.utils.html import strip_tags

LANGUAGE_CHOICES = [
    ('de', 'Deutsch'),
    ('en', 'English'),
]

APARTMENT_COLORS = [
    "#ff6666",  # 🍓 Rot
    "#66b3ff",  # 🌊 Blau
    "#99ff99",  # 🌿 Grün
    "#ffcc99",  # 🌅 Orange
    "#c299ff",  # 🌸 Lila
    "#ffff99",  # 🌞 Gelb
    "#cccccc",  # ⚪️ Grau
]


class Lender(models.Model):
    first_name = models.CharField("Vorname", max_length=50)
    last_name = models.CharField("Nachname", max_length=50)
    address = models.CharField("Adresse (Straße & Hausnummer)", max_length=120)
    postal_code = models.CharField("PLZ", max_length=10)
    city = models.CharField("Ort", max_length=50, default="Berlin")
    country = models.CharField("Land", max_length=50)
    email = models.EmailField()
    mobile = models.CharField("Mobiltelefon", max_length=20, blank=True)
    whatsapp = models.CharField("WhatsApp", max_length=20, blank=True)
    language = models.CharField("Sprache", max_length=2, choices=LANGUAGE_CHOICES, default='de')
    discount_percent = models.DecimalField("Rabatt in %", max_digits=5, decimal_places=2, default=Decimal('0.0'))

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def current_balance(self):
        total_payments = sum(p.amount_eur() for p in self.payments.all())
        total_bookings = sum(b.total_cost() for b in self.bookings.all())
        return (total_payments - total_bookings).quantize(Decimal('0.01'))


class Loan(models.Model):
    LOAN_TYPE_CHOICES = [
        ('flexible', 'Flexibles Darlehen'),
        ('fixed', 'Festes Darlehen'),
    ]

    lender = models.ForeignKey(Lender, on_delete=models.CASCADE, related_name='loans')
    loan_type = models.CharField(max_length=10, choices=LOAN_TYPE_CHOICES)
    target_amount = models.DecimalField("Zielbetrag (nur bei festen Darlehen)", max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.lender} – {self.loan_type} – {self.created_at.strftime('%Y-%m-%d')}"


class Payment(models.Model):
    lender = models.ForeignKey(Lender, on_delete=models.CASCADE, related_name='payments')
    date = models.DateField()
    original_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, choices=[('EUR', 'Euro'), ('USD', 'US Dollar')])
    exchange_rate = models.DecimalField("Wechselkurs (nur bei USD)", max_digits=6, decimal_places=4, default=Decimal('1.0'))
    loan = models.ForeignKey('Loan', on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')

    def amount_eur(self):
        return (self.original_amount * self.exchange_rate).quantize(Decimal('0.01')) if self.currency == 'USD' else self.original_amount

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if not self.loan:
            loan, created = Loan.objects.get_or_create(
                lender=self.lender,
                loan_type='flexible',
                defaults={'created_at': self.date}
            )
            self.loan = loan
        super().save(*args, **kwargs)

        if is_new:
            activate(self.lender.language)  # optional, nur falls du Templates direkt danach brauchst

class PaymentEmailLog(models.Model):
    payment = models.OneToOneField("Payment", on_delete=models.CASCADE, related_name="email_log")
    sent_at = models.DateTimeField(auto_now_add=True)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES)

    def __str__(self):
        return f"E-Mail für {self.payment} am {self.sent_at:%Y-%m-%d %H:%M}"

class Apartment(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price_per_night = models.DecimalField(max_digits=7, decimal_places=2)
    is_active = models.BooleanField(default=True)
    color = models.CharField("Farbe (für Kalender)", max_length=7, default="#cccccc")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Automatische Farbvergabe nur wenn keine gesetzt ist oder default verwendet wird
        if not self.color or self.color == "#cccccc":
            existing_colors = set(Apartment.objects.values_list("color", flat=True))
            for color in APARTMENT_COLORS:
                if color not in existing_colors:
                    self.color = color
                    break
        is_new = self.pk is None
        if not self.loan:
            loan, _ = Loan.objects.get_or_create(
                lender=self.lender,
                loan_type='flexible',
                defaults={'created_at': self.date}
            )
            self.loan = loan
        super().save(*args, **kwargs)

        if is_new:
            activate(self.lender.language)
            subject = {
                "de": "💰 Zahlungseingang bestätigt",
                "en": "💰 Payment Received"
            }.get(self.lender.language, "Payment Received")
 
        # Daten für die Mail
        payments = self.lender.payments.order_by("date")
        bookings = self.lender.bookings.order_by("start_date")
        context = {
            "lender": self.lender,
            "payment": self,
            "payments": payments,
            "bookings": bookings,
            "balance": self.lender.current_balance(),
            "language": self.lender.language
        }

        html_content = render_to_string(f"emails/payment_confirmation_{self.lender.language}.html", context)
        text_content = render_to_string(f"emails/payment_confirmation_{self.lender.language}.txt", context)

        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [self.lender.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)

        # Logging
        from .models import PaymentEmailLog
        PaymentEmailLog.objects.create(payment=self, language=self.lender.language)
        # Kontextdaten für die Mail
        context = {
            "lender": self.lender,
            "payment": self,
            "all_payments": self.lender.payments.order_by("date"),
            "all_bookings": self.lender.bookings.order_by("start_date"),
            "saldo": self.lender.current_balance(),
        }

        # E-Mail Inhalte generieren
        subject = render_to_string("emails/payment_subject.txt", context).strip()
        text_body = render_to_string("emails/payment_body.txt", context)
        html_body = render_to_string("emails/payment_body.html", context)

        # E-Mail senden
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email="CBV Goodwill <noreply@cbvgoodwill.de>",
            to=[self.lender.email],
        )
        email.attach_alternative(html_body, "text/html")
        email.send()


class SeasonalRate(models.Model):
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, related_name='seasonal_rates')
    start_date = models.DateField()
    end_date = models.DateField()
    percentage_adjustment = models.DecimalField("Preis-Anpassung in %", max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.apartment.name}: {self.start_date} bis {self.end_date} – {self.percentage_adjustment:+.0f} %"

    def adjusted_price(self):
        base = self.apartment.price_per_night
        return (base * (Decimal("1") + self.percentage_adjustment / Decimal("100"))).quantize(Decimal("0.01"))


class Booking(models.Model):
    lender = models.ForeignKey(Lender, on_delete=models.CASCADE, related_name='bookings')
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    custom_total_price = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, verbose_name="Pauschalpreis (optional)")
    override_confirm = models.BooleanField(default=False, verbose_name="Ich bestätige die Warnung manuell")

    def __str__(self):
        return f"{self.lender} – {self.apartment} – {self.start_date} bis {self.end_date}"

    def nights(self):
        return (self.end_date - self.start_date).days

    def get_seasonal_price(self):
        if not self.apartment or not self.start_date or not self.end_date:
            return None
        overlapping_rate = self.apartment.seasonal_rates.filter(
            start_date__lte=self.start_date,
            end_date__gte=self.end_date
        ).first()
        if overlapping_rate:
            return overlapping_rate.adjusted_price()
        return None

    def price_per_night_after_discount(self):
        if self.apartment.name == "La Villa Complete" and self.custom_total_price:
            return self.custom_total_price
        seasonal_price = self.get_seasonal_price()
        base_price = seasonal_price or self.apartment.price_per_night
        discount = self.lender.discount_percent or Decimal('0')
        return (base_price * (Decimal('1') - discount / Decimal('100'))).quantize(Decimal('0.01'))

    def total_cost(self):
        if self.apartment.name == "La Villa Complete" and self.custom_total_price:
            return self.custom_total_price.quantize(Decimal('0.01'))
        return (Decimal(self.nights()) * self.price_per_night_after_discount()).quantize(Decimal('0.01'))

    def clean(self):
        super().clean()

        if self.apartment and self.start_date and self.end_date:
            overlapping = Booking.objects.filter(
                apartment=self.apartment,
                start_date__lt=self.end_date,
                end_date__gt=self.start_date,
            ).exclude(id=self.id)

            if overlapping.exists():
                raise ValidationError(
                    _("❌ Diese Buchung überschneidet sich mit einer bestehenden Buchung von %(apartment)s."),
                    code='overlap',
                    params={'apartment': self.apartment.name},
                )

            if self.apartment.name.strip().lower() == "la villa complete":
                other_apartments = Apartment.objects.exclude(name__iexact="La Villa Complete")
                all_occupied = True

                for apt in other_apartments:
                    if not Booking.objects.filter(
                        apartment=apt,
                        start_date__lt=self.end_date,
                        end_date__gt=self.start_date,
                    ).exists():
                        all_occupied = False
                        break

                if all_occupied and not self.override_confirm:
                    raise ValidationError(
                        _("❌ Die Buchung von 'La Villa Complete' ist nur erlaubt, wenn mindestens ein anderes Apartment frei ist oder die Warnung bewusst bestätigt wurde."),
                        code='villa_blocked'
                    )
    
class SentConfirmation(models.Model):
    lender = models.ForeignKey("Lender", on_delete=models.CASCADE)
    payment = models.ForeignKey("Payment", on_delete=models.CASCADE)
    sent_at = models.DateTimeField(auto_now_add=True)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES)
    recipient = models.EmailField()

    def __str__(self):
        return f"{self.lender} – {self.payment.date} – {self.sent_at.strftime('%Y-%m-%d %H:%M')}"
