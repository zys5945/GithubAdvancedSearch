import requests
import datetime
import time
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
        response = session.send(request)

        if response.headers['X-RateLimit-Remaining'] == 0:
            reset_time = datetime.datetime.fromtimestamp(response.headers['X-RateLimit-Reset'])
            print('exceeded query limit rate, the next reset is {}, sleeping until then...'.format(
               reset_time.strftime('%H:%M:%S')
            ))
            if response.headers['X-RateLimit-Limit'] == 60:
                print('note you can raise the limit of request per hour to 5000 if you authenticate yourself')
            time.sleep((reset_time - datetime.datetime.now()).total_seconds() + 1)

        return response