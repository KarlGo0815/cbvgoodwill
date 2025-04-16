from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

LANGUAGE_CHOICES = [
    ('de', 'Deutsch'),
    ('en', 'English'),
]


class Lender(models.Model):
    first_name = models.CharField("Vorname", max_length=50)
    last_name = models.CharField("Nachname", max_length=50)
    street = models.CharField("Straße", max_length=100)
    house_number = models.CharField("Hausnummer", max_length=10)
    postal_code = models.CharField("PLZ", max_length=10)
    country = models.CharField("Land", max_length=50)
    email = models.EmailField()
    mobile = models.CharField("Mobiltelefon", max_length=20, blank=True)
    whatsapp = models.CharField("WhatsApp", max_length=20, blank=True)
    language = models.CharField("Sprache", max_length=2, choices=LANGUAGE_CHOICES, default='de')
    discount_percent = models.DecimalField("Rabatt in %", max_digits=5, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def current_balance(self):
        total_payments = sum(p.amount_eur() for p in self.payments.all())
        total_bookings = sum(b.total_cost() for b in self.bookings.all())
        return round(total_payments - total_bookings, 2)


class Loan(models.Model):
    LOAN_TYPE_CHOICES = [
        ('flexible', 'Flexibles Darlehen'),
        ('fixed', 'Festes Darlehen'),
    ]

    lender = models.ForeignKey(Lender, on_delete=models.CASCADE, related_name='loans')
    loan_type = models.CharField(max_length=10, choices=LOAN_TYPE_CHOICES)
    target_amount = models.DecimalField(
        "Zielbetrag (nur bei festen Darlehen)",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.lender} – {self.loan_type} – {self.created_at.strftime('%Y-%m-%d')}"


class Payment(models.Model):
    lender = models.ForeignKey(Lender, on_delete=models.CASCADE, related_name='payments')
    date = models.DateField()
    original_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, choices=[('EUR', 'Euro'), ('USD', 'US Dollar')])
    exchange_rate = models.DecimalField("Wechselkurs (nur bei USD)", max_digits=6, decimal_places=4, default=1.0)
    loan = models.ForeignKey('Loan', on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')

    def amount_eur(self):
        return self.original_amount * self.exchange_rate if self.currency == 'USD' else self.original_amount

    def save(self, *args, **kwargs):
        if not self.loan:
            loan, created = Loan.objects.get_or_create(
                lender=self.lender,
                loan_type='flexible',
                defaults={'created_at': self.date}
            )
            self.loan = loan
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.lender} – {self.date} – {self.original_amount} {self.currency}"


class Apartment(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price_per_night = models.DecimalField(max_digits=7, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class SeasonalRate(models.Model):
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, related_name='seasonal_rates')
    start_date = models.DateField()
    end_date = models.DateField()
    price_per_night = models.DecimalField(max_digits=7, decimal_places=2)

    def __str__(self):
        return f"{self.apartment.name}: {self.start_date} bis {self.end_date} – {self.price_per_night} €"

class Booking(models.Model):
    lender = models.ForeignKey(Lender, on_delete=models.CASCADE, related_name='bookings')
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    # 🔧 Optional: Pauschalpreis z. B. für „La Villa Complete“
    custom_total_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Pauschalpreis (optional)"
    )

    def __str__(self):
        return f"{self.lender} – {self.apartment} – {self.start_date} bis {self.end_date}"

    def nights(self):
        return (self.end_date - self.start_date).days

    def get_seasonal_price(self):
        """Ermittelt ggf. den passenden Saisonpreis."""
        if not self.apartment:
            return None
        overlapping_rate = self.apartment.seasonal_rates.filter(
            start_date__lte=self.start_date,
            end_date__gte=self.end_date
        ).first()
        return overlapping_rate.price_per_night if overlapping_rate else None

    def price_per_night_after_discount(self):
        # Sonderfall: "La Villa Complete" mit Pauschalpreis
        if self.apartment.name == "La Villa Complete" and self.custom_total_price:
            return self.custom_total_price

        # Standard- oder Saisonpreis
        seasonal_price = self.get_seasonal_price()
        base_price = seasonal_price or self.apartment.price_per_night
        discount = self.lender.discount_percent or 0
        return base_price * (1 - discount / 100)

    def total_cost(self):
        # Sonderfall: "La Villa Complete" mit Pauschalpreis
        if self.apartment.name == "La Villa Complete" and self.custom_total_price:
            return round(self.custom_total_price, 2)

        # Standardberechnung
        return round(self.nights() * self.price_per_night_after_discount(), 2)

    def clean(self):
        from django.core.exceptions import ValidationError
        from django.utils.translation import gettext_lazy as _

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

    def __str__(self):
        return f"{self.lender} – {self.apartment} – {self.start_date} bis {self.end_date}"
