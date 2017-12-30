import requests

from toot.logging import log_request, log_response
from requests import Request, Session
from toot.exceptions import NotFoundError, ApiError


def process_response(response):
    log_response(response)

    if not response.ok:
        error = "Unknown error"

        try:
            data = response.json()
            if "error_description" in data:
                error = data['error_description']
            elif "error" in data:
                error = data['error']
        except Exception:
            pass

        if response.status_code == 404:
            raise NotFoundError(error)

        raise ApiError(error)

    return response


def get(app, user, url, params=None):
    url = app.base_url + url
    headers = {"Authorization": "Bearer " + user.access_token}

    log_request(Request('GET', url, headers, params=params))

    response = requests.get(url, params, headers=headers)

    return process_response(response)


def unauthorized_get(url, params=None):
    log_request(Request('GET', url, None, params=params))

    response = requests.get(url, params)

    return process_response(response)


def post(app, user, url, data=None, files=None):
    url = app.base_url + url
    headers = {"Authorization": "Bearer " + user.access_token}

    session = Session()
    request = Request('POST', url, headers, files, data)
    prepared_request = request.prepare()

    log_request(request)

    response = session.send(prepared_request)

    return process_response(response)
