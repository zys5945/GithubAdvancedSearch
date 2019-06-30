import requests
import datetime
import time
import math
from urllib.parse import urljoin


base_url = "https://api.github.com/"


def send(method, url, headers=None, json=None):
    """wait on rate limit exceeded
    Returns:
        requests.Response
    """

    url = urljoin(base_url, url)

    session = requests.Session()

    request = requests.Request(method, url, headers=headers, json=json)

    while True:
        response = session.send(session.prepare_request(request))

        if response.headers['X-RateLimit-Remaining'] == 0:
            reset_time = datetime.datetime.fromtimestamp(response.headers['X-RateLimit-Reset'])
            print('exceeded query limit rate, the next reset is {}, sleeping until then...'.format(
               reset_time.strftime('%H:%M:%S')
            ))
            if response.headers['X-RateLimit-Limit'] == 60:
                print('note you can raise the limit of request per hour to 5000 if you authenticate yourself')
            time.sleep((reset_time - datetime.datetime.now()).total_seconds() + 1)

        return response




def scroll(method, url, headers=None, json=None, max_items=None, per_page=100):
    """query results by scrolling

    max_items
        if None then get all items, otherwise only these many (integer) items are fetched

        note only a maximum of 1000 items can be retrieved

    Returns:
        list<items>
    """

    page = 1 # page starts at one, trippy
    total_item_count = max_items
    overlap = 0

    items = []

    while True: # scroll through all pages
        paged_query_url = url + '&per_page={0}&page={1}'.format(per_page, page)

        result = send(method, paged_query_url, headers=headers, json=json).json()

        # parse response

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

    return items