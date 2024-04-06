"""
Helpers for testing.
"""

import time
from typing import Callable, TypeVar


T = TypeVar("T")


def run_with_retries(fn: Callable[..., T]) -> T:
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

    return fn()
