from datetime import date


def time_to_date(time):  # Time is in hours.
    return date.fromordinal(time // 24)
