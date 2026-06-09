"""
Core utilities.
"""

from decimal import Decimal, ROUND_HALF_UP


def round_money(value: Decimal, decimal_places: int = 0) -> Decimal:
    """
    Round monetary value using banker's rounding.

    Args:
        value: Decimal value to round
        decimal_places: Number of decimal places (default 0 for UZS)

    Returns:
        Rounded Decimal value
    """
    if not isinstance(value, Decimal):
        value = Decimal(str(value))

    quantize_str = '1' if decimal_places == 0 else f'0.{"0" * decimal_places}'
    return value.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)


def calculate_working_days(start_date, end_date, holidays=None):
    """
    Calculate working days between two dates.

    Args:
        start_date: Start date
        end_date: End date
        holidays: List of holiday dates (optional)

    Returns:
        Number of working days
    """
    from datetime import timedelta

    if holidays is None:
        holidays = []

    working_days = 0
    current_date = start_date

    while current_date <= end_date:
        # 5 = Saturday, 6 = Sunday
        if current_date.weekday() < 5 and current_date not in holidays:
            working_days += 1
        current_date += timedelta(days=1)

    return working_days


def format_money(value: Decimal) -> str:
    """
    Format money value for display.

    Args:
        value: Decimal value

    Returns:
        Formatted string (e.g., "1 200 000")
    """
    if value is None:
        return "0"

    # Round to whole number (UZS has no cents)
    rounded = round_money(value)

    # Format with space as thousands separator
    return f"{rounded:,.0f}".replace(",", " ")
