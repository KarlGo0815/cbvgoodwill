# lenders/utils.py
from django.http import HttpResponse
from django.urls import path
from django.core.mail import send_mail

def sende_testmail(empfaenger):
    send_mail(
        subject="CBV-Goodwill – Testmail 💌",
        message="Das ist ein Test vom Render-Server.",
        from_email=None,  # oder explizit: 'info@deine-domain.de'
        recipient_list=[empfaenger],
        fail_silently=False,
    )