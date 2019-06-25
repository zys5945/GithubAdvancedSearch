import copy
from enum import Enum
import requests

class AuthType(Enum):
    OAUTH_TOKEN = 0

class AuthCreds:
    @staticmethod
    def oauth(oauth_token):
        auth = AuthCreds()

        auth._creds = oauth_token
        auth._auth_type = AuthType.OAUTH_TOKEN

        return auth

    def __init__(self):
        self._auth_type = None

    def clone(self):
        auth = AuthCreds()

        auth._creds = copy.deepcopy(self._creds)
        auth._auth_types = copy.deepcopy(self._auth_types)

        return auth

    def write_headers(self, prepared_request):
        if self._auth_type is None:
            raise ValueError('Credentials must first be specified')

        if not isinstance(prepared_request, requests.PreparedRequest):
            raise ValueError('Expecting a PreparedRequest, got {}'.format(prepared_request))

        headers = self.get_headers()
        prepared_request.headers.update(headers)

    def get_headers(self):
        if self._auth_type is None:
            raise ValueError('Credentials must first be specified')

        if self._auth_type is AuthType.OAUTH_TOKEN:
            return {
                'Authorization': 'token {0}'.format(self._creds)
            }
        else:
            raise ValueError('Unsupported auth type {}'.format(self._auth_type.name))

    def is_oauth(self):
        return self._auth_type is AuthType.OAUTH_TOKEN