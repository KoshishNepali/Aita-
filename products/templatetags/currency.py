from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django import template


register = template.Library()


@register.filter(name='npr')
def npr(value):
    """Format numeric value as Nepali Rupees display format."""
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return 'NPR 0.00'

    formatted = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return f"NPR {formatted:,.2f}"
