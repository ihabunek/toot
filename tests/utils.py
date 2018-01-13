import requests


class Expectations():
    """Helper for mocking http requests"""
    def __init__(self, requests=[], responses=[]):
        self.requests = requests
        self.responses = responses

    def mock_prepare(self, request):
        expected = self.requests.pop(0)
        assert request.method == expected.method
        assert request.url == expected.url
        assert request.data == expected.data
        assert request.headers == expected.headers
        assert request.params == expected.params

    def mock_send(self, *args, **kwargs):
        return self.responses.pop(0)

    def add(self, req, res):
        self.requests.append(req)
        self.responses.append(res)

    def patch(self, monkeypatch):
        monkeypatch.setattr(requests.Session, 'prepare_request', self.mock_prepare)
        monkeypatch.setattr(requests.Session, 'send', self.mock_send)


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
