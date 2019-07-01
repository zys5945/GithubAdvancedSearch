from .search_request import SearchRequest
from ..auth import AuthCreds, AuthType
from ..v3 import scroll

class RepositorySearch(SearchRequest):
    def __init__(self):
        super().__init__()

    def clone(self):
        obj = super().clone()

        return obj

    def execute(self):
        query_url = 'search/repositories' + self.get_url_parameters()

        return scroll('GET', query_url, self.get_auth_headers())

    def in_(self, val):
        return self.must('in', range)

    def stars(self, range):
        return self.must('stars', range)