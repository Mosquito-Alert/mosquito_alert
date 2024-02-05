from datetime import datetime, date, timedelta
import pytz

from django.utils import timezone


def apply_tz_to_datetime(value: datetime, tz: pytz.timezone) -> datetime:
    # If tz = None, will use the one configured in settings
    if timezone.is_aware(value):
        value = timezone.make_naive(value)

    return timezone.make_aware(value, timezone=tz, is_dst=False)


def is_instant_upload_candidate(
    server_creation_datetime: datetime, user_creation_datetime: datetime
) -> bool:
    # The UTC offset for time zones ranges from UTC-12:00 to UTC+14:00,
    # so even if the minutes and hour are the same, it's not considered
    # to be an instant upload
    upload_diff = server_creation_datetime - user_creation_datetime
    if upload_diff < timedelta(hours=-12) or upload_diff > timedelta(hours=14):
        return False

    # Cast datetimes to timedeltas (only take into account minutes,seconds,microseconds)
    server_timedelta = (
        datetime.combine(date.min, server_creation_datetime.time().replace(hour=0))
        - datetime.min
    )
    user_timedelta = (
        datetime.combine(date.min, user_creation_datetime.time().replace(hour=0))
        - datetime.min
    )

    # Assumption is that server_timedelta is going to be slightly ahead of user_timedelta.
    # That is due to the client first save the timestamp after posting the object,
    # and after the server receives it.

    # When the client_time is ahead the server_time.
    # For example if client_time is 00:27:31 and server is 00:11:00, will return False.
    # In that case, the phone was missconfigured, cause the server can not receive
    # future dates. In any case, we know this can happend, and a tolerance of 30seconds
    # is accepted. So if client_time is 00:27:31 and server is 00:27:02, will return True
    NEGATIVE_TOLERANCE = timedelta(seconds=30)

    # When the server_time is ahead the client_time
    # Delay between when the client posted the objects and when it was received by the server.
    # When server_time is expected to be ahead that client_time
    POSITIVE_TOLERANCE = timedelta(minutes=2)

    # Consider also timezones with XX:30:00h offset.
    ROUND_BY = timedelta(minutes=30)
    return (
        ((server_timedelta - user_timedelta) % ROUND_BY) + NEGATIVE_TOLERANCE
    ) % ROUND_BY <= (POSITIVE_TOLERANCE + NEGATIVE_TOLERANCE)
