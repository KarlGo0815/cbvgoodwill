# lenders/templatetags/currency_filters.py
from django import template

register = template.Library()

@register.filter
def eur(value):
    """
    Formatiert eine Zahl im deutschen Format mit Euro-Zeichen:
    1234.5 → 1.234,50 €
    """
    try:
        value = float(value)
        formatted = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{formatted} €"
    except (ValueError, TypeError):
        return value
