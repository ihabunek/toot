"""
Helpers for testing.
"""


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
