from django import template

register = template.Library()

@register.filter
def get_average(exams):
    """Calculate average marks from a queryset of exams."""
    if not exams:
        return 0
    total = sum(exam.marks for exam in exams)
    return total / len(exams) if exams else 0

@register.filter
def get_highest_marks(exams):
    """Get the highest marks from a queryset of exams."""
    if not exams:
        return 0
    return max(exam.marks for exam in exams)

@register.filter
def get_lowest_marks(exams):
    """Get the lowest marks from a queryset of exams."""
    if not exams:
        return 0
    return min(exam.marks for exam in exams)

@register.filter
def div(value, arg):
    """Divide value by arg."""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def sub(value, arg):
    """Subtract arg from value."""
    try:
        return float(value) - float(arg)
    except ValueError:
        return 0

@register.filter
def mul(value, arg):
    """Multiply value by arg."""
    try:
        return float(value) * float(arg)
    except ValueError:
        return 0
