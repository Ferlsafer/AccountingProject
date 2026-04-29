from decimal import Decimal
from django import template

register = template.Library()


@register.simple_tag
def currency(amount):
    from core.models import Business
    if amount is None:
        amount = Decimal('0')
    business = Business.get_solo()
    if business.base_currency == 'TZS':
        return f"TZS {int(amount):,}"
    return f"$ {Decimal(amount):,.2f}"


@register.filter
def currency_filter(amount):
    from core.models import Business
    if amount is None:
        amount = Decimal('0')
    business = Business.get_solo()
    if business.base_currency == 'TZS':
        return f"TZS {int(amount):,}"
    return f"$ {Decimal(amount):,.2f}"
