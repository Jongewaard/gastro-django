from django import template
from datetime import datetime, timedelta

register = template.Library()


@register.filter
def dict_get(dictionary, key):
    """
    Safely get a value from a dictionary by key.
    Usage: {{ my_dict|dict_get:key }}
    Returns None if the dictionary is not a dict or key doesn't exist.
    """
    if not isinstance(dictionary, dict):
        return None
    return dictionary.get(key)


@register.simple_tag
def total_hours(emp_schedules):
    """
    Calculate total scheduled hours for an employee's weekly schedule.
    emp_schedules: dict of {date_str: schedule_obj}
    Each schedule_obj should have shift_start, shift_end, and break_minutes attributes.
    Returns total hours as a rounded number.
    """
    if not isinstance(emp_schedules, dict):
        return 0

    total_minutes = 0
    for date_str, sched in emp_schedules.items():
        try:
            start = sched.shift_start
            end = sched.shift_end

            if start and end:
                # Convert time objects to datetime for calculation
                start_dt = datetime.combine(datetime.today(), start)
                end_dt = datetime.combine(datetime.today(), end)

                # Handle overnight shifts
                if end_dt <= start_dt:
                    end_dt += timedelta(days=1)

                diff = (end_dt - start_dt).total_seconds() / 60
                break_mins = getattr(sched, 'break_minutes', 0) or 0
                total_minutes += diff - break_mins
        except (AttributeError, TypeError, ValueError):
            continue

    hours = round(total_minutes / 60, 1)
    # Return as int if whole number, else keep one decimal
    if hours == int(hours):
        return int(hours)
    return hours
