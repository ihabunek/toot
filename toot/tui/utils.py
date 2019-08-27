import re

from datetime import datetime

HASHTAG_PATTERN = re.compile(r'(?<!\w)(#\w+)\b')


def highlight_hashtags(line):
    return [
        ("hashtag", p) if p.startswith("#") else p
        for p in re.split(HASHTAG_PATTERN, line)
    ]


def parse_datetime(value):
    """Returns an aware datetime in local timezone"""
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z").astimezone()
