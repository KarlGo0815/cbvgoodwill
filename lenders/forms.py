from django import forms
from django.utils.safestring import mark_safe
from .models import Booking, Lender, Apartment
from datetime import datetime
from decimal import Decimal


class BookingAdminForm(forms.ModelForm):
    warning_html = ""

    class Meta:
        model = Booking
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.warning_html = ""

        try:
            lender_id = self.data.get("lender") or getattr(self.instance, "lender_id", None)
            apartment_id = self.data.get("apartment") or getattr(self.instance, "apartment_id", None)
            start = self.data.get("start_date") or getattr(self.instance, "start_date", None)
            end = self.data.get("end_date") or getattr(self.instance, "end_date", None)

            if not (lender_id and apartment_id and start and end):
                self.warning_html = mark_safe(
                    "<div style='background-color:#ffffcc; color:black; padding:10px; border:1px solid #cccc00;'>"
                    "ℹ️ Bitte wähle <strong>Lender</strong>, <strong>Appartement</strong>, <strong>Startdatum</strong> und "
                    "<strong>Enddatum</strong> aus, um die Guthabenprüfung durchzuführen."
                    "</div>"
                )
                self.instance.form = self
                return

            lender = Lender.objects.get(id=lender_id)
            apartment = Apartment.objects.get(id=apartment_id)

            if isinstance(start, str):
                start = datetime.strptime(start, "%Y-%m-%d").date()
            if isinstance(end, str):
                end = datetime.strptime(end, "%Y-%m-%d").date()

            nights = (end - start).days
            rabatt = lender.discount_percent or Decimal('0')
            preis = apartment.price_per_night
            kosten = (Decimal(nights) * preis * (Decimal('1') - rabatt / Decimal('100'))).quantize(Decimal('0.01'))
            saldo = lender.current_balance()

            # ⚠️ Guthabenwarnung
            if nights > 0 and kosten > saldo:
                self.warning_html += mark_safe(
                    f"""
                    <div style='border: 2px solid red; background-color: #ffe5e5; color: black; padding: 10px; margin-bottom: 15px;'>
                        <strong>⚠️ Achtung:</strong> Das aktuelle Guthaben beträgt <strong>{saldo:.2f} €</strong>,
                        aber die Buchung kostet <strong>{kosten:.2f} €</strong>.
                    </div>
                    """
                )

            # 📌 La Villa Complete Spezialhinweis
            if apartment.name.strip().lower() == "la villa complete":
                self.warning_html += mark_safe(
                    """
                    <div style='border: 2px solid #3174ad; background-color: #e8f0fe; color: #000; padding: 10px; margin-top: 10px;'>
                        <strong>📌 Hinweis:</strong> 'La Villa Complete' darf nur gebucht werden, wenn mindestens
                        <em>eine andere Wohnung</em> (z.B. App en Villa oder App en Nave) <u>frei</u> ist.
                        Mit der Checkbox unten kannst du diese Warnung übergehen.
                    </div>
                    """
                )

        except Exception as e:
            self.warning_html += mark_safe(
                f"<div style='color:red;'>⚠️ Fehler bei der Guthabenprüfung: {e}</div>"
            )

        # Wichtig für Zugriff im Admin
        self.instance.form = self


class LenderAdminForm(forms.ModelForm):
    class Meta:
        model = Lender
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Nur bestimmte Felder erforderlich machen
        required_fields = ["first_name", "last_name", "email", "language"]
        for field_name in self.fields:
            self.fields[field_name].required = field_name in required_fields
