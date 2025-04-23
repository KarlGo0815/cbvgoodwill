from ..email_utils import send_custom_email
import logging

logger = logging.getLogger(__name__)

def send_html_email(subject, recipient, context, html_template, text_template=None):
    """
    Wrapper für rückwärtskompatiblen Mailversand.
    Intern wird send_custom_email verwendet.
    """
    language = context.get("language", "de")

    try:
        send_custom_email(
            recipient=recipient,
            subject=subject,
            template_name=html_template,
            context=context,
            language=language
        )
        logger.info(f"📤 E-Mail erfolgreich gesendet an {recipient} mit Template {html_template}")
        return True
    except Exception as e:
        logger.error(f"❌ Fehler beim E-Mail-Versand an {recipient}: {e}")
        return False
