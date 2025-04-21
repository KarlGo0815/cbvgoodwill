from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import activate
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import Booking, Payment, SentConfirmation
from .utils.email_helpers import send_html_email

import logging
logger = logging.getLogger(__name__)

@receiver(post_save, sender=Payment)
def send_payment_confirmation(sender, instance, created, **kwargs):
    if not created:
        return

    logger.info(f"📥 Neue Zahlung erkannt: ID {instance.pk}, Betrag {instance.original_amount} {instance.currency}")

    lender = instance.lender
    activate(lender.language)

    context = {
        "lender": lender,
        "payment": instance,
        "payments": lender.payments.order_by("date"),
        "bookings": lender.bookings.order_by("start_date"),
        "balance": lender.current_balance(),
        "language": lender.language
    }

    subject = {
        "de": "💰 Zahlungseingang bestätigt",
        "en": "💰 Payment received"
    }.get(lender.language, "💰 Payment received")

    if send_html_email(subject, lender.email, context,
                       f"emails/payment_confirmation_{lender.language}.html"):
        SentConfirmation.objects.create(
            lender=lender,
            payment=instance,
            language=lender.language,
            recipient=lender.email
        )
        logger.info(f"📤 Zahlungs-E-Mail erfolgreich gesendet an {lender.email}")
    else:
        logger.warning(f"❌ Zahlungs-E-Mail konnte nicht gesendet werden an {lender.email}")


@receiver(post_save, sender=Booking)
def send_booking_confirmation(sender, instance, created, **kwargs):
    if not created:
        logger.debug(f"✋ Buchung {instance.pk} wurde aktualisiert, kein E-Mail-Versand.")
        return

    logger.info(f"📆 Neue Buchung erkannt: ID {instance.pk}, Zeitraum {instance.start_date}–{instance.end_date}")

    lender = instance.lender
    activate(lender.language)

    context = {
        "lender": lender,
        "booking": instance,
        "bookings": lender.bookings.order_by("start_date"),
        "payments": lender.payments.order_by("date"),
        "balance": lender.current_balance(),
        "language": lender.language,
    }

    subject = {
        "de": "📅 Buchungsbestätigung – Casa Bella Vista",
        "en": "📅 Booking Confirmation – Casa Bella Vista"
    }.get(lender.language, "📅 Booking Confirmation")

    if send_html_email(
        subject,
        lender.email,
        context,
        html_template=f"emails/booking_confirmation_{lender.language}.html",
        text_template=f"emails/booking_confirmation_{lender.language}.txt"
    ):
        SentConfirmation.objects.create(
            lender=lender,
            booking=instance,
            language=lender.language,
            recipient=lender.email
        )
        logger.info(f"📤 Buchungs-E-Mail erfolgreich gesendet an {lender.email}")
    else:
        logger.warning(f"❌ Buchungs-E-Mail konnte nicht gesendet werden an {lender.email}")
