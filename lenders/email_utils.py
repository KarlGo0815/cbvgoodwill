from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import activate
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_custom_email(
    recipient,
    subject,
    template_name,
    context=None,
    language="de"
):
    """
    Sendet eine HTML-E-Mail mit Plaintext-Fallback über Django.
    
    Args:
        recipient (str): E-Mail-Adresse des Empfängers.
        subject (str): Betreff der E-Mail.
        template_name (str): Pfad zum HTML-Template.
        context (dict): Kontextdaten fürs Template.
        language (str): Sprachauswahl (z. B. 'de' oder 'en').
    
    Returns:
        True bei Erfolg, False bei Fehler.
    """
    if not recipient:
        raise ValueError("Empfängeradresse fehlt.")

    activate(language)
    context = context or {}

    try:
        html_content = render_to_string(template_name, context)
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()

        logger.info(f"📧 E-Mail erfolgreich gesendet an {recipient} (Betreff: '{subject}')")
        return True
    except Exception as e:
        logger.error(f"❌ Fehler beim E-Mail-Versand an {recipient}: {e}")
        return False
