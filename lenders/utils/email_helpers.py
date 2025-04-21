from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_html_email(subject, recipient, context, html_template, text_template=None):
    try:
        html_content = render_to_string(html_template, context)
        text_content = render_to_string(text_template, context) if text_template else strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        return True
    except Exception as e:
        logger.error(f"❌ Fehler beim E-Mail-Versand an {recipient}: {e}")
        return False
