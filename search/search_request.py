from copy import deepcopy
from ..auth import AuthCreds
from ..request import GithubRequest

class SearchRequest(GithubRequest):
    def __init__(self):
        self._qualifiers = [] # list of (option, value)
        self._keywords = [] # list of actual keywords, each keyword must not contain spaces
        self._first = None

        self._auth_creds = None

    def clone(self):
        obj = type(self)()

        obj._qualifiers = deepcopy(self._qualifiers)
        obj._keywords = deepcopy(self._keywords)
        obj._first = deepcopy(self._first)
        obj._auth_creds = None if self._auth_creds is None else self._auth_creds.clone()

        return obj

    def first(self, num):
        if num < 0:
            raise RuntimeError('illegal value {0}'.format(num))
        self._first = num
        return self

    def auth(self, auth_creds):
        if not isinstance(auth_creds, AuthCreds):
            raise ValueError('Expecting an AuthCreds, got {}'.format(auth_creds))

        self._auth_creds = auth_creds

        return self

    def must(self, option, value):
        self._qualifiers.append((option, value))
        return self

    def keywords(self, keyword):
        self._keywords += list(filter(None, keyword.split(' ')))