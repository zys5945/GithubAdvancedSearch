from functools import reduce
import math
import copy
import gql
import gql.transport.requests as gql_requests
import requests
import time
import math

from ..auth import AuthCreds, AuthType
from ..v3 import send as send_v3
from ..v4 import send as send_v4
from .cross_filter import cross_filter

class PrAndIssueSearch:
    def __init__(self):
        self._qualifiers = [] # list of (option, value)
        self._keywords = [] # list of actual keywords, each keyword must not contain spaces

        self._auth_creds = None
        self._first = None

        self._fields = None
        self._fragments = None

        self._results = None
        self._result_node_id_to_index = None

    def clone(self):
        clone = PrAndIssueSearch()

        clone._qualifiers = copy.deepcopy(self._qualifiers)
        clone._keywords = copy.deepcopy(self._keywords)

        clone._auth_creds = None if clone._auth_creds is None else self._auth_creds.clone()
        clone._first = copy.deepcopy(self._first)

        clone._fields = copy.deepcopy(self._fields)
        clone._fragments = copy.deepcopy(self._fragments)

        clone._results = copy.deepcopy(self._results)
        clone._result_node_id_to_index = copy.deepcopy(self._result_node_id_to_index)

        return clone

    # metadata

    def auth(self, auth_creds):
        if not isinstance(auth_creds, AuthCreds):
            raise ValueError('Expecting an AuthCreds, got {}'.format(auth_creds))

        self._auth_creds = auth_creds

        return self

    def first(self, num):
        if num < 0:
            raise RuntimeError('illegal value {0}'.format(num))
        self._first = num
        return self

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

        per_page = 100 # maximum of 100 results can be returned per request
        page = 1 # page starts at one, trippy
        total_item_count = None if self._first is None else self._first
        overlap = 0

        items = []

        while True: # scroll through all pages
            paged_query_url = query_url + '&per_page={0}&page={1}'.format(per_page, page)

            result = send_v3('GET', paged_query_url,headers=None if self._auth_creds is None else self._auth_creds.get_headers()).json()

            # parse return

            cur_items = None

            # deal with overlap
            if overlap == 0:
                cur_items = result['items']
            else:
                cur_items = result['items'][overlap:]

            # resolve total item count
            if total_item_count is None or total_item_count > result['total_count']:
                total_item_count = result['total_count']

            if total_item_count > 1000:
                print(('query matched {0} results but only the first 1000 search results are available,'
                      ' auto-truncating to 1000').format(total_item_count))
                total_item_count = 1000

            items += cur_items
            total_item_acquired = len(items)

            print('received {0} out of {1} items'.format(total_item_acquired, total_item_count))

            # break if gotten all items or we paged past the last item
            if total_item_acquired >= total_item_count or page * per_page >= total_item_count:
                break

            # if query is incomplete, set per_page to a smaller number and try again
            if result['incomplete_results']:
                returned_item_length = len(cur_items)

                per_page = returned_item_length
                page = math.floor(total_item_acquired / returned_item_length)
                overlap = total_item_acquired - page * per_page
            else:
                # got requested items
                page += 1

        if len(items) > total_item_count:
            items = items[:total_item_count]

        self._results = items
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

        gql_query = """
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

        nodes_fields = send_v4(gql_query)['nodes']

        for i, node_fields in enumerate(nodes_fields):
            self._results[self._result_node_id_to_index[node_ids[i]]]['fields'] = node_fields

        return self._results


    # query composing methods
    
    def must(self, option, value):
        self._qualifiers.append((option, value))
        return self

    def keywords(self, keyword):
        self._keywords += list(filter(None, keyword.split(' ')))

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
        return self.must('user', username)

    def org(self, orgname):
        return self.must('org', orgname)

    def repo(self, reponame):
        return self.must('repo', reponame)

    def is_(self, val):
        return self.must('is', val)

    def type(self, type):
        return self.must('type', type)

    def state(self, state):
        return self.must('state', state)

    def label(self, label):
        return self.must('label', label)

    def status(self, status):
        return self.must('status', status)

    def review(self, review_status):
        return self.must('review', review_status)

    def created(self, date_range_expression):
        return self.must('created', date_range_expression)

    def updated(self, date_range_expression):
        return self.must('updated', date_range_expression)

    def closed(self, date_range_expression):
        return self.must('closed', date_range_expression)

    def merged(self, date_range_expression):
        return self.must('merged', date_range_expression)

    def head(self, branch_name):
        return self.must('head', branch_name)

    def base(self, branch_name):
        return self.must('base', branch_name)

    def language(self, language):
        return self.must('language', language)

    def comments(self, range_expression):
        return self.must('comments', range_expression)

    def no(self, metadata):
        return self.must('no', metadata)

    def milestone(self, milestone):
        return self.must('milestone', milestone)

    def project(self, project_board_number):
        return self.must('project', project_board_number)

    def involves(self, username):
        return self.must('involves', username)

    def author(self, username):
        return self.must('author', username)

    def assignee(self, username):
        return self.must('assignee', username)

    def commenter(self, username):
        return self.must('commenter', username)

    def mentions(self, username):
        return self.must('mentions', username)

    def team(self, teamname):
        return self.must('team', teamname)

    def in_(self, place):
        return self.must('in', place)

    def review_by(self, username):
        return self.must('review-by', username)

    def review_requested(self, username):
        return self.must('review-requested', username)

    def team_review_requested(self, teamname):
        return self.must('team-review-requested', teamname)

    # other utility methods

    def cross_filter(self, search_result, fn):
        if self._results is None:
            return []

        return cross_filter(self._results, search_result, fn)


__all__ = [ 'PrAndIssueSearch' ]