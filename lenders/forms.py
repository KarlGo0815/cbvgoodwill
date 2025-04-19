from django import forms
from django.utils.safestring import mark_safe
from .models import Booking, Lender, Apartment
from datetime import datetime


class BookingAdminForm(forms.ModelForm):
    warning_html = ""

    class Meta:
        model = Booking
        fields = "__all__"

    override_confirm = forms.BooleanField(
        label="Warnung übersteuern – ich bestätige bewusst",
        required=False
    )

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
                    "<div style='background-color:#ffffcc; padding:10px;'>ℹ️ Bitte alle Felder ausfüllen, um die Prüfung zu aktivieren.</div>"
                )
                return

            lender = Lender.objects.get(id=lender_id)
            apartment = Apartment.objects.get(id=apartment_id)

            if isinstance(start, str):
                start = datetime.strptime(start, "%Y-%m-%d").date()
            if isinstance(end, str):
                end = datetime.strptime(end, "%Y-%m-%d").date()

            nights = (end - start).days
            preis = apartment.price_per_night
            rabatt = lender.discount_percent or 0
            kosten = round(nights * float(preis) * (1 - float(rabatt) / 100), 2)
            saldo = lender.current_balance()

            if nights > 0 and kosten > saldo:
                self.warning_html += mark_safe(
                    f"""
                    <div style='border: 2px solid red; background-color: #ffe5e5; padding: 10px; margin: 10px 0;'>
                        ⚠️ Das aktuelle Guthaben beträgt <strong>{saldo:.2f} €</strong>,
                        aber die Buchung kostet <strong>{kosten:.2f} €</strong>.
                    </div>
                    """
                )

            if apartment.name.strip().lower() == "la villa complete":
                # Prüfe ob andere Apartments frei sind
                other_apartments = Apartment.objects.exclude(name__iexact="La Villa Complete")
                all_occupied = True
                for apt in other_apartments:
                    if not Booking.objects.filter(
                        apartment=apt,
                        start_date__lt=end,
                        end_date__gt=start,
                    ).exists():
                        all_occupied = False
                        break

                if all_occupied:
                    self.warning_html += mark_safe(
                        """
                        <div style='border: 2px solid orange; background-color: #fff3cd; padding: 10px; margin-top: 10px;'>
                            ⚠️ Achtung: <strong>Alle anderen Apartments sind im gewünschten Zeitraum belegt.</strong><br>
                            Die Buchung von <strong>La Villa Complete</strong> sollte nur in Ausnahmefällen erfolgen.<br>
                            Bitte aktiv das Häkchen setzen, um fortzufahren.
                        </div>
                        """
                    )

        except Exception as e:
            self.warning_html = mark_safe(
                f"<div style='color:red;'>⚠️ Fehler bei der Prüf-Logik: {e}</div>"
            )

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
