import json
from urllib import parse

import requests


class APIError(Exception):
    def __init__(self, message=None, http_body=None, http_status=None,
                 json_body=None, headers=None):
        super(APIError, self).__init__(message)

        if http_body and hasattr(http_body, 'decode'):
            http_body = http_body.decode('utf-8')

        self._message = message
        self.http_body = http_body
        self.http_status = http_status
        self.json_body = json_body
        self.headers = headers or {}

    def __str__(self):
        return self._message


class StepikAPIRequestor(object):
    def __init__(self, api_base=None):
        self.api_base = api_base
        self.token = None

    def connect(self, client_id, client_secret):
        auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
        resp = requests.post('{}/oauth2/token/'.format(self.api_base),
                             data={'grant_type': 'client_credentials'},
                             auth=auth)
        token = resp.json().get('access_token')
        if not token:
            raise RuntimeWarning('Client id/secret is probably incorrect')

        self.token = token
        return True

    def request(self, method, url, params=None, json_data=None):
        response = self.request_raw(method.lower(), url, params, json_data)
        body, code, headers = response.content, response.status_code, response.headers
        resp = self.handle_response(body, code, headers)
        return resp

    @staticmethod
    def handle_api_error(body, code, resp, headers):
        try:
            err = resp['error']
        except (KeyError, TypeError):
            raise APIError('Invalid response object from API({}): {}'.format(code, body), body, code, resp)

        raise APIError(err.get('message'), body, code, resp, headers)

    def request_raw(self, method, url, params=None, json_data=None):
        if not self.token:
            raise APIError('Try to request without token')

        request_url = '{}{}'.format(self.api_base, url)

        if method == 'get':
            if params:
                query = dict_to_tuples(params)
                request_url = '{}?{}'.format(request_url, parse.urlencode(list(query)))
        elif method == 'put':
            if params:
                print('unsupported')
        elif method == 'post':
            if params:
                print('unsupported')
        else:
            raise APIError('Unrecognized HTTP method {}'.format(method))

        headers = {'Authorization': 'Bearer ' + self.token}

        return requests.request(method, request_url, headers=headers, json=json_data)

    def handle_response(self, body, code, headers):
        try:
            if hasattr(body, 'decode'):
                body = body.decode('utf-8')
            resp = json.loads(body)
        except Exception:
            raise APIError('Invalid response body from API({}): {}'.format(code, body), body, code, headers)
        if code != 200 and code != 201:
            self.handle_api_error(body, code, resp, headers)
        return resp


def dict_to_tuples(data):
    for key, value in data.items():
        if value is None:
            continue
        else:
            yield (key, value)
