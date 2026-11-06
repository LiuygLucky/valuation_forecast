from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")


def utc(value: str | datetime) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("TIME_NOT_VERIFIED: timezone required")
    return dt.astimezone(UTC)


def local_time(day: date, hour: int = 13) -> datetime:
    return datetime.combine(day, time(hour), ET).astimezone(UTC)


def availability_reason(source: dict, as_of: datetime, archived: bool = False) -> str | None:
    cutoff = utc(as_of)
    public = source.get("first_public_at") or source.get("published_at")
    if not public:
        return "QUARANTINED_TIME_UNKNOWN"
    seen = source.get("first_seen_at")
    capture = source.get("archive_capture_at")
    if archived and capture and source.get("archive_verified"):
        seen = capture
    if not seen:
        return "QUARANTINED_TIME_UNKNOWN"
    # A revision has its own publication/capture time; the source's old date cannot bless it.
    times = [public, seen, source.get("published_at")]
    if not (archived and capture and source.get("archive_verified")):
        times.append(source.get("captured_at"))
    else:
        times.append(capture)
    if any(utc(t) > cutoff for t in times if t is not None):
        return "EXCLUDED_FUTURE"
    return None
