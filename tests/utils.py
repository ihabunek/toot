
class MockResponse:
    def __init__(self, response_data={}, ok=True):
        self.ok = ok
        self.response_data = response_data

    def raise_for_status(self):
        pass

    def json(self):
        return self.response_data
