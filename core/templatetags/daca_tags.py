from django import template

register = template.Library()

@register.filter(name='clp')
def clp(value):
    """
    Format a number as Chilean Pesos: $12.990 (no decimals, dot thousand separator).
    """
    if value is None or value == '':
        return '$0'
    try:
        val = int(round(float(value)))
        formatted = f"{val:,}".replace(",", ".")
        return f"${formatted}"
    except (ValueError, TypeError):
        return f"${value}"

@register.filter(name='clp_raw')
def clp_raw(value):
    """
    Format a number as Chilean Pesos without dollar symbol: 12.990
    """
    if value is None or value == '':
        return '0'
    try:
        val = int(round(float(value)))
        return f"{val:,}".replace(",", ".")
    except (ValueError, TypeError):
        return str(value)
