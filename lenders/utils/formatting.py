# lenders/utils/formatting.py

def format_eur(amount):
    """Formatiert einen Betrag als deutsche Währung, z. B. 1234.56 → 1.234,56"""
    return f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
