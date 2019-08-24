import re

HASHTAG_PATTERN = re.compile(r'(?<!\w)(#\w+)\b')


def highlight_hashtags(line):
    return [
        ("hashtag", p) if p.startswith("#") else p
        for p in re.split(HASHTAG_PATTERN, line)
    ]
