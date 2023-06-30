import math
import os

from datetime import datetime, timezone


def parse_datetime(value):
    """Returns an aware datetime in local timezone"""
    dttm = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z")

    # When running tests return datetime in UTC so that tests don't depend on
    # the local timezone
    if "PYTEST_CURRENT_TEST" in os.environ:
        return dttm.astimezone(timezone.utc)

    return dttm.astimezone()


SECOND = 1
MINUTE = SECOND * 60
HOUR = MINUTE * 60
DAY = HOUR * 24
WEEK = DAY * 7


def time_ago(value: datetime) -> str:
    now = datetime.now().astimezone()
    delta = now.timestamp() - value.timestamp()

    if delta < 1:
        return "now"

    if delta < 8 * DAY:
        if delta < MINUTE:
            return f"{math.floor(delta / SECOND)}".rjust(2, " ") + "s"
        if delta < HOUR:
            return f"{math.floor(delta / MINUTE)}".rjust(2, " ") + "m"
        if delta < DAY:
            return f"{math.floor(delta / HOUR)}".rjust(2, " ") + "h"
        return f"{math.floor(delta / DAY)}".rjust(2, " ") + "d"

    if delta < 53 * WEEK:  # not exactly correct but good enough as a boundary
        return f"{math.floor(delta / WEEK)}".rjust(2, " ") + "w"

    return ">1y"
