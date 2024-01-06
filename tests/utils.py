"""
Helpers for testing.
"""

import time
from typing import Any, Callable


class MockResponse:
    def __init__(self, response_data={}, ok=True, is_redirect=False):
        self.response_data = response_data
        self.content = response_data
        self.ok = ok
        self.is_redirect = is_redirect

    def raise_for_status(self):
        pass

    def json(self):
        return self.response_data


def retval(val):
    return lambda *args, **kwargs: val


def run_with_retries(fn: Callable[..., Any]):
    """
    Run the the given function repeatedly until it finishes without raising an
    AssertionError. Sleep a bit between attempts. If the function doesn't
    succeed in the given number of tries raises the AssertionError. Used for
    tests which should eventually succeed.
    """

    # Wait upto 6 seconds with incrementally longer sleeps
    delays = [0.1, 0.2, 0.3, 0.4, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]

    for delay in delays:
        try:
            return fn()
        except AssertionError:
            time.sleep(delay)

    fn()
