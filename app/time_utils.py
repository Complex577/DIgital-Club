from datetime import datetime, timedelta

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

