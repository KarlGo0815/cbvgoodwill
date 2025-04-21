from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class LendersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lenders'
    verbose_name = _("Menue - Auswahlbereich")  # 👈 Das wird im Admin angezeigt
def ready(self):
    import lenders.signals  # wichtig!
