from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import activate
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import Booking, Payment, SentConfirmation
from .utils.email_helpers import send_html_email
from .email_utils import send_custom_email
from lenders.utils.formatting import format_eur

import logging
logger = logging.getLogger(__name__)

@receiver(post_save, sender=Payment)
def send_payment_confirmation(sender, instance, created, **kwargs):
    if not created:
        return

    lender = instance.lender
    language = lender.language or "de"
    activate(language)

    logger.info(f"📥 Neue Zahlung erkannt: ID {instance.pk}, Betrag {instance.original_amount} {instance.currency}")

    context = {
        "lender": lender,
        "payment": instance,
        "balance": format_eur(lender.current_balance()),
        "formatted_amount": format_eur(instance.original_amount),
        "language": language
    }

    subject = {
        "de": "💰 Zahlungseingang bestätigt",
        "en": "💰 Payment received"
    }.get(language, "💰 Payment received")

    try:
        send_custom_email(
            recipient=lender.email,
            subject=subject,
            template_name=f"emails/payment_confirmation_{language}.html",
            context=context,
            language=language
        )
        SentConfirmation.objects.create(
            lender=lender,
            payment=instance,
            language=language,
            recipient=lender.email
        )
        logger.info(f"📤 Zahlungs-E-Mail erfolgreich gesendet an {lender.email}")
    except Exception as e:
        logger.warning(f"❌ Fehler beim Senden der Zahlungs-E-Mail an {lender.email}: {e}")


@receiver(post_save, sender=Booking)
def send_booking_confirmation(sender, instance, created, **kwargs):
    if not created:
        logger.debug(f"✋ Buchung {instance.pk} wurde aktualisiert, kein E-Mail-Versand.")
        return

    lender = instance.lender
    language = lender.language or "de"
    activate(language)

    logger.info(f"📆 Neue Buchung erkannt: ID {instance.pk}, Zeitraum {instance.start_date}–{instance.end_date}")

    context = {
        "lender": lender,
        "booking": instance,
        "bookings": lender.bookings.order_by("start_date"),
        "payments": lender.payments.order_by("date"),
        "balance": format_eur(lender.current_balance()),
        "formatted_total_cost": format_eur(instance.total_cost()),
        "language": language,
    }

    subject = {
        "de": "📅 Buchungsbestätigung – Casa Bella Vista",
        "en": "📅 Booking Confirmation – Casa Bella Vista"
    }.get(language, "📅 Booking Confirmation")

    try:
        send_custom_email(
            recipient=lender.email,
            subject=subject,
            template_name=f"emails/booking_confirmation_{language}.html",
            context=context,
            language=language
        )
        SentConfirmation.objects.create(
            lender=lender,
            booking=instance,
            language=language,
            recipient=lender.email
        )
        logger.info(f"📤 Buchungs-E-Mail erfolgreich gesendet an {lender.email}")
    except Exception as e:
        logger.warning(f"❌ Fehler beim Senden der Buchungs-E-Mail an {lender.email}: {e}")
