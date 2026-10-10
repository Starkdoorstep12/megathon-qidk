from datetime import datetime, timedelta

WD = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}


def resolve_parts(day, hour, minute, now):
    ref = now if isinstance(now, datetime) else datetime.fromisoformat(str(now)[:19])
    ref = ref.replace(tzinfo=None)
    base = ref.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if day == "today":
        dt = base
    elif day == "yesterday":
        dt = base - timedelta(days=1)
    elif day.endswith("_days_ago"):
        dt = base - timedelta(days=int(day.split("_")[0]))
    elif day in WD:
        delta = (ref.weekday() - WD[day]) % 7 or 7
        dt = base - timedelta(days=delta)
    else:  # unspecified: most recent past occurrence of that clock time
        dt = base - timedelta(days=1) if base > ref else base
    return dt.isoformat(timespec="seconds")
