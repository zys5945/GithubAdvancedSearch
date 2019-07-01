from functools import reduce
import math
import copy
import requests
import time
import math

from .search_request import SearchRequest
from ..auth import AuthCreds, AuthType
from ..v3 import send as send_v3, scroll
from ..v4 import send as send_v4
from .cross_filter import cross_filter

class PrAndIssueSearch(SearchRequest):
    def __init__(self):
        super().__init__()

        self._fields = None
        self._fragments = None

        self._results = None
        self._result_node_id_to_index = None

    def clone(self):
        clone = super().clone()

        clone._fields = copy.deepcopy(self._fields)
        clone._fragments = copy.deepcopy(self._fragments)

        clone._results = copy.deepcopy(self._results)
        clone._result_node_id_to_index = copy.deepcopy(self._result_node_id_to_index)

        return clone

    # execution

    def execute(self):
        '''
        this is a two part operation because github graphql api currently does not support all of the qualifiers that the rest api supports, thus we need to get all the node_id from rest api, then query graphql for the specific fields
        '''
        self._query_rest_api()

        if self._fields is not None:
            if self._auth_creds is None or not self._auth_creds.is_oauth():
                raise RuntimeError('oauth token must be provided if graphql api is used')

            self._query_graphql()

        return self._results

    def _query_rest_api(self):
        '''
        populate self._results with an array containing all items matching the search criteria
        for the specific structure of each object in the array, refer to github api https://developer.github.com/v3/#pagination
        each element also contains an extra property named "fields", which contains all the fields from graphql
        '''
        query_url = 'search/issues' + \
                    '?q=' + \
                    '+'.join(self._keywords) + \
                    '+'.join(
                        map(
                            lambda pair: pair[0] + ':"' + pair[1] + '"',
                            self._qualifiers
                        )
                    )

        self._results = scroll('GET', query_url, None if self._auth_creds is None else self._auth_creds.get_headers())
        
        self._result_node_id_to_index = {}

        for i, result in enumerate(self._results):
            self._result_node_id_to_index[result['node_id']] = i

        return self._results

    def _query_graphql(self):
        all_node_ids = list(map(lambda result: result['node_id'], self._results))

        for i in range(math.ceil(len(all_node_ids) / 100)): # only 100 ids can be queried at once
            self._query_graphql_using_ids(all_node_ids[i * 100: (i + 1) * 100])

        return self._results

    def _query_graphql_using_ids(self, node_ids):
        node_ids_string = '[ ' + reduce(lambda prev, next: prev + '"' + str(next) + '", ', node_ids, '') + ']'

        gql_query = {
            'query': """
            {{
                nodes(ids: {0}){{
                    {1}
                }}
            }}
            {2}
            """.format(
                node_ids_string,
                self._fields,
                ('' if self._fragments is None else self._fragments),
            )
        }

        nodes_fields = send_v4(gql_query, self._auth_creds.get_headers()).json()['data']['nodes']

        for i, node_fields in enumerate(nodes_fields):
            self._results[self._result_node_id_to_index[node_ids[i]]]['fields'] = node_fields

        return self._results


    # query composing methods
    
    def fields(self, fields, fragments=None):
        '''
        set fields for the graphql query
        fields and fragments should be gql strings
        i.e.
        {
            nodes {
                <fields go here>
            }
        }
        <fragments go here>
        '''
        self._fields = fields
        self._fragments = fragments
        return self

    # convenience query construction methods

    def user(self, username):
        return super().must('user', username)

    def org(self, orgname):
        return super().must('org', orgname)

    def repo(self, reponame):
        return super().must('repo', reponame)

    def is_(self, val):
        return super().must('is', val)

    def type(self, type):
        return super().must('type', type)

    def state(self, state):
        return super().must('state', state)

    def label(self, label):
        return super().must('label', label)

    def status(self, status):
        return super().must('status', status)

    def review(self, review_status):
        return super().must('review', review_status)

    def created(self, date_range_expression):
        return super().must('created', date_range_expression)

    def updated(self, date_range_expression):
        return super().must('updated', date_range_expression)

    def closed(self, date_range_expression):
        return super().must('closed', date_range_expression)

    def merged(self, date_range_expression):
        return super().must('merged', date_range_expression)

    def head(self, branch_name):
        return super().must('head', branch_name)

    def base(self, branch_name):
        return super().must('base', branch_name)

    def language(self, language):
        return super().must('language', language)

    def comments(self, range_expression):
        return super().must('comments', range_expression)

    def no(self, metadata):
        return super().must('no', metadata)

    def milestone(self, milestone):
        return super().must('milestone', milestone)

    def project(self, project_board_number):
        return super().must('project', project_board_number)

    def involves(self, username):
        return super().must('involves', username)

    def author(self, username):
        return super().must('author', username)

    def assignee(self, username):
        return super().must('assignee', username)

    def commenter(self, username):
        return super().must('commenter', username)

    def mentions(self, username):
        return super().must('mentions', username)

    def team(self, teamname):
        return super().must('team', teamname)

    def in_(self, place):
        return super().must('in', place)

    def review_by(self, username):
        return super().must('review-by', username)

    def review_requested(self, username):
        return super().must('review-requested', username)

    def team_review_requested(self, teamname):
        return super().must('team-review-requested', teamname)

    # other utility methods

    def cross_filter(self, search_result, fn):
        if self._results is None:
            return []

        return cross_filter(self._results, search_result, fn)


__all__ = [ 'PrAndIssueSearch' ]