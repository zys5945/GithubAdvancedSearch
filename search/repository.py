from .search_request import SearchRequest
from ..auth import AuthCreds, AuthType
from ..v3 import send as send_v3

class RepositorySearch(SearchRequest):
    def __init__(self):
        super().__init__()

    def clone(self):
        pass

    def auth(self):
        pass

    def execute(self):
        pass