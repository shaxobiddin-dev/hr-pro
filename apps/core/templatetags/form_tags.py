"""
Custom template tags for forms.
"""

from django import template

register = template.Library()

# Field name to label mapping
FIELD_LABELS = {
    # Order form fields
    'order_number': 'Buyruq raqami',
    'order_date': 'Buyruq sanasi',
    'approved_by': 'Tasdiqlovchi',
    'legal_basis': 'Asos',
    'notes': 'Izohlar',

    # HiringOrderItem fields
    'employee': 'Xodim',
    'department': "Bo'lim",
    'position': 'Lavozim',
    'start_date': 'Ish boshlash sanasi',
    'end_date': 'Tugash sanasi',
    'salary': 'Oylik maosh',
    'work_schedule': 'Ish tartibi',
    'has_probation': 'Sinov muddati',
    'probation_end_date': 'Sinov tugash sanasi',
    'probation_salary': 'Sinov oyligi',
    'probation_department': "Sinov bo'limi",
    'probation_position': 'Sinov lavozimi',
    'contract_number': 'Shartnoma raqami',
    'contract_date': 'Shartnoma sanasi',

    # New employee fields
    'new_first_name': 'Ism',
    'new_last_name': 'Familiya',
    'new_email': 'Email',
    'is_new_employee': 'Yangi xodim',

    # Common fields
    'email': 'Email',
    'first_name': 'Ism',
    'last_name': 'Familiya',
    'phone': 'Telefon',
    'status': 'Holat',
    'date': 'Sana',
    'check_in': 'Kelish vaqti',
    'check_out': 'Ketish vaqti',
    'reason': 'Sabab',
    'code': 'Kod',
    'name': 'Nomi',
}


@register.filter
def field_label(form, field_name):
    """
    Get human-readable label for a field.
    Usage: {{ form|field_label:field_name }}
    """
    # First try to get label from form field
    if hasattr(form, 'fields') and field_name in form.fields:
        label = form.fields[field_name].label
        if label:
            return label

    # Then try our mapping
    if field_name in FIELD_LABELS:
        return FIELD_LABELS[field_name]

    # Fallback: return field name with underscores replaced
    return field_name.replace('_', ' ').title()
