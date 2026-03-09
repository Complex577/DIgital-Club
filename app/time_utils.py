from datetime import datetime, timedelta, timezone

from flask import current_app

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None


def app_now_naive():
    """
    Return application-local current time as a naive datetime.
    Stored schedule datetimes in this app are naive local times, so comparisons
    should use the same basis.
    """
    tz_name = (current_app.config.get("APP_TIMEZONE") or "").strip()
    if tz_name and ZoneInfo is not None:
        try:
            return datetime.now(ZoneInfo(tz_name)).replace(tzinfo=None)
        except Exception:
            pass

    # Fallback: fixed offset, defaults to UTC+3 for KIUT deployment context.
    try:
        offset = int(current_app.config.get("APP_UTC_OFFSET_HOURS", 3))
    except Exception:
        offset = 3
    return datetime.utcnow() + timedelta(hours=offset)


def utc_to_app_naive(value):
    """
    Convert a UTC datetime into application-local naive datetime.

    Datetimes persisted in DB are stored as UTC (typically naive), while UI
    rendering expects local wall-clock time.
    """
    if value is None:
        return None

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)

    tz_name = (current_app.config.get("APP_TIMEZONE") or "").strip()
    if tz_name and ZoneInfo is not None:
        try:
            return value.astimezone(ZoneInfo(tz_name)).replace(tzinfo=None)
        except Exception:
            pass

    try:
        offset = int(current_app.config.get("APP_UTC_OFFSET_HOURS", 3))
    except Exception:
        offset = 3
    return (value + timedelta(hours=offset)).replace(tzinfo=None)


def app_timezone_label():
    """Return a short display label for the configured app timezone."""
    tz_name = (current_app.config.get("APP_TIMEZONE") or "").strip()
    if tz_name in {"Africa/Nairobi", "Africa/Dar_es_Salaam", "Africa/Kampala"}:
        return "EAT"
    return tz_name or f"UTC+{current_app.config.get('APP_UTC_OFFSET_HOURS', '3')}"
