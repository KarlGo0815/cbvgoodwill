from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import activate
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

from .models import Payment, SentConfirmation

import logging
logger = logging.getLogger(__name__)

@receiver(post_save, sender=Payment)
def send_payment_confirmation(sender, instance, created, **kwargs):
    if not created:
        return

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

    try:
        html_content = render_to_string(f"emails/payment_confirmation_{lender.language}.html", context)
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[lender.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()

        SentConfirmation.objects.create(
            lender=lender,
            payment=instance,
            language=lender.language,
            recipient=lender.email
        )
    except Exception as e:
        logger.error(f"Fehler beim Senden der Zahlungsbestätigung für Zahlung {instance.id}: {e}")
