from urllib.parse import urlencode, urlparse

from requests import Request, Session
from requests.exceptions import RequestException

from toot import __version__
from toot.exceptions import ApiError, NotFoundError
from toot.logging import log_request, log_request_exception, log_response


def send_request(request, allow_redirects=True):
    # Set a user agent string
    # Required for accessing instances using Cloudfront DDOS protection.
    request.headers["User-Agent"] = "toot/{}".format(__version__)

    log_request(request)

    try:
        with Session() as session:
            prepared = session.prepare_request(request)
            settings = session.merge_environment_settings(prepared.url, {}, None, None, None)
            response = session.send(prepared, allow_redirects=allow_redirects, **settings)
    except RequestException as ex:
        log_request_exception(request, ex)
        raise ApiError(f"Request failed: {str(ex)}")

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

    return f"Unknown error: {response.status_code} {response.reason}"


def process_response(response):
    if not response.ok:
        error = _get_error_message(response)

        if response.status_code == 404:
            raise NotFoundError(error)

        raise ApiError(error)

    return response


def get(app, user, path, params=None, headers=None):
    url = app.base_url + path

    headers = headers or {}
    headers["Authorization"] = f"Bearer {user.access_token}"

    request = Request('GET', url, headers, params=params)
    response = send_request(request)

    return process_response(response)


def get_paged(app, user, path, params=None, headers=None):
    if params:
        path += f"?{urlencode(params)}"

    while path:
        response = get(app, user, path, headers=headers)
        yield response
        path = _next_path(response)


def _next_path(response):
    next_link = response.links.get("next")
    if next_link:
        next_url = urlparse(next_link["url"])
        return "?".join([next_url.path, next_url.query])


def anon_get(url, params=None):
    request = Request('GET', url, None, params=params)
    response = send_request(request)

    return process_response(response)


def anon_get_paged(url, params=None):
    if params:
        url += f"?{urlencode(params)}"

    while url:
        response = anon_get(url)
        yield response
        url = _next_url(response)


def _next_url(response):
    next_link = response.links.get("next")
    if next_link:
        return next_link["url"]


def post(app, user, path, headers=None, files=None, data=None, json=None, allow_redirects=True):
    url = app.base_url + path

    headers = headers or {}
    headers["Authorization"] = f"Bearer {user.access_token}"

    return anon_post(url, headers=headers, files=files, data=data, json=json, allow_redirects=allow_redirects)


def anon_put(url, headers=None, files=None, data=None, json=None, allow_redirects=True):
    request = Request(method="PUT", url=url, headers=headers, files=files, data=data, json=json)
    response = send_request(request, allow_redirects)

    return process_response(response)


def put(app, user, path, headers=None, files=None, data=None, json=None, allow_redirects=True):
    url = app.base_url + path

    headers = headers or {}
    headers["Authorization"] = f"Bearer {user.access_token}"

    return anon_put(url, headers=headers, files=files, data=data, json=json, allow_redirects=allow_redirects)


def patch(app, user, path, headers=None, files=None, data=None, json=None):
    url = app.base_url + path

    headers = headers or {}
    headers["Authorization"] = f"Bearer {user.access_token}"

    request = Request('PATCH', url, headers=headers, files=files, data=data, json=json)
    response = send_request(request)

    return process_response(response)


def delete(app, user, path, data=None, json=None, headers=None):
    url = app.base_url + path

    headers = headers or {}
    headers["Authorization"] = f"Bearer {user.access_token}"

    request = Request('DELETE', url, headers=headers, data=data, json=json)
    response = send_request(request)

    return process_response(response)


def anon_post(url, headers=None, files=None, data=None, json=None, allow_redirects=True):
    request = Request(method="POST", url=url, headers=headers, files=files, data=data, json=json)
    response = send_request(request, allow_redirects)

    return process_response(response)
