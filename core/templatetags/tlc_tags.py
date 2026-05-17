from decimal import Decimal
from django import template

register = template.Library()


def _safe_amount(amount):
    if not amount and amount != 0:
        return Decimal('0')
    try:
        return Decimal(str(amount))
    except Exception:
        return Decimal('0')


@register.simple_tag
def currency(amount):
    from core.models import Business
    amount = _safe_amount(amount)
    business = Business.get_solo()
    if business.base_currency == 'TZS':
        return f"TZS {int(amount):,}"
    return f"$ {amount:,.2f}"


@register.filter
def currency_filter(amount):
    from core.models import Business
    amount = _safe_amount(amount)
    business = Business.get_solo()
    if business.base_currency == 'TZS':
        return f"TZS {int(amount):,}"
    return f"$ {amount:,.2f}"
