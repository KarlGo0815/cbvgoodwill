from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import activate
from django.conf import settings
from .models import Payment, Booking
from .models import SentConfirmation

@receiver(post_save, sender=Payment)
def send_payment_confirmation(sender, instance, created, **kwargs):
    if not created:
        return

    lender = instance.lender
    activate(lender.language)

    all_payments = lender.payments.order_by("date")
    total_paid = sum(p.amount_eur() for p in all_payments)
    bookings = lender.bookings.all()
    total_used = sum(b.total_cost() for b in bookings)
    balance = total_paid - total_used

    context = {
        "lender": lender,
        "payment": instance,
        "all_payments": all_payments,
        "total_paid": f"{total_paid:.2f}",
        "bookings": bookings,
        "total_used": f"{total_used:.2f}",
        "balance": f"{balance:.2f}",
        "language": lender.language,
    }

    subject = {
        "de": "Zahlungsbestätigung – Casa Bella Vista",
        "en": "Payment Confirmation – Casa Bella Vista"
    }.get(lender.language, "Payment Confirmation")

    html_content = render_to_string("emails/payment_confirmation.html", context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body="Vielen Dank für Ihre Zahlung." if lender.language == "de" else "Thank you for your payment.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[lender.email],
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()
SentConfirmation.objects.create(
    lender=lender,
    payment=instance,
    language=lender.language,
    recipient=lender.email
)