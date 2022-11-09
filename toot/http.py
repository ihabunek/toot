from requests import Request, Session
from toot import __version__
from toot.exceptions import NotFoundError, ApiError
from toot.logging import log_request, log_response


def send_request(request, allow_redirects=True):
    # Set a user agent string
    # Required for accessing instances using Cloudfront DDOS protection.
    request.headers["User-Agent"] = "toot/{}".format(__version__)

    log_request(request)

    with Session() as session:
        prepared = session.prepare_request(request)
        settings = session.merge_environment_settings(prepared.url, {}, None, None, None)
        response = session.send(prepared, allow_redirects=allow_redirects, **settings)

    log_response(response)

    return response


def _get_error_message(response):
    """Attempt to extract an error message from response body"""
    try:
        data = response.json()
        if "error_description" in data:
            return data['error_description']
        if "error" in data:
            return data['error']
    except Exception:
        pass

    return "Unknown error"


def process_response(response):
    if not response.ok:
        error = _get_error_message(response)

        if response.status_code == 404:
            raise NotFoundError(error)

        raise ApiError(error)

    return response


def get(app, user, url, params=None):
    url = app.base_url + url
    headers = {"Authorization": "Bearer " + user.access_token}

    request = Request('GET', url, headers, params=params)
    response = send_request(request)

    return process_response(response)


def anon_get(url, params=None):
    request = Request('GET', url, None, params=params)
    response = send_request(request)

    return process_response(response)


def post(app, user, url, data=None, files=None, allow_redirects=True, headers={}):
    url = app.base_url + url

    headers["Authorization"] = "Bearer " + user.access_token

    request = Request('POST', url, headers, files, data)
    response = send_request(request, allow_redirects)

    return process_response(response)


def delete(app, user, url, data=None):
    url = app.base_url + url
    headers = {"Authorization": "Bearer " + user.access_token}

    request = Request('DELETE', url, headers=headers, data=data)
    response = send_request(request)

    return process_response(response)


def anon_post(url, data=None, files=None, allow_redirects=True):
    request = Request('POST', url, {}, files, data)
    response = send_request(request, allow_redirects)

    return process_response(response)
