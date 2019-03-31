from enum import Enum
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import requests
import time
import math

rest_base_url = "https://api.github.com/"

rest_search_issue_and_pr_url = rest_base_url + "search/issues"

gql_url = "https://api.github.com/graphql"


class PrAndIssueSearch:
    def __init__(self):
        self._qualifiers = [] # list of (option, value)
        self._keywords = [] # list of actual keywords, each keyword must not contain spaces
        self._oauth_token = None
        self._first = None
        self._fields = None

    # metadata

    def oauth(self, token):
        self._oauth_token = token
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

        if self._fields != None:
            self._query_graphql()

        return self.results

    def _query_rest_api(self):
        '''
        populate self.results with an array containing all items matching the search criteria
        for the specific structure of each object in the array, refer to github api https://developer.github.com/v3/#pagination
        each element also contains an extra property named "fields", which contains all the fields from graphql
        '''
        query_url = rest_search_issue_and_pr_url + \
                    '?q=' + \
                    '+'.join(self._keywords) + \
                    '+'.join(
                        map(
                            lambda pair: pair[0] + ':"' + pair[1] + '"',
                            self._qualifiers
                        )
                    )

        per_page = 100
        page = 1 # page starts at one, trippy
        total_item_count = None if self._first is None else self._first
        overlap = 0

        items = []

        while True: # scroll through all pages
            result = self._query_until_success(self._append_page_param(query_url, per_page, page))

            cur_items = None

            # deal with overlap
            if overlap == 0:
                cur_items = result['items']
            else:
                cur_items = result['items'][overlap:]

            print(result)

            # resolve total item count
            if total_item_count is None:
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

        self.results = items
        return results

    def _exceeded_limit(self, result):
        '''
        :param result: object parsed from json response
        :return: true if limit exceeded
        '''
        return result.get('message') is not None

    def _query_until_success(self, query_url):
        while True:
            result = requests.get(query_url, headers={
                'Authorization' : 'token {0}'.format(self._oauth_token)
            }).json()

            if self._exceeded_limit(result):
                print('exceeded query limit rate, waiting for 1 minute before continuing...')
                if self._oauth_token is None:
                    print('you can increase the request per hour to 5000 if you provide an oauth token')
                time.sleep(60000)
            else:
                return result

    def _append_page_param(self, query_url, per_page, page):
        return query_url + '&per_page={0}&page={1}'.format(per_page, page)

    def _query_graphql(self):
        node_ids = map(lambda result: result['node_id'], self.results)

    # query composing methods
    
    def must(self, option, value):
        self._qualifiers.append((option, value))
        return self

    def keywords(self, keyword):
        self._keywords += list(filter(None, keyword.split(' ')))

    def fields(self, fields):
        '''
        set fields for the graphql query
        fields should be a string that specifies the fields to retrieve
        i.e.
        {
            nodes {
                <fields go here>
            }
        }
        '''
        self._fields = fields

    # convenience methods

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


__all__ = [ 'PrAndIssueSearch' ]