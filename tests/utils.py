
class MockResponse:
    def __init__(self, response_data={}):
        self.response_data = response_data

    def raise_for_status(self):
        pass

    def json(self):
        return self.response_data
