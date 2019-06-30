import datetime
import requests

base_url = "https://api.github.com/graphql"

def send(json, headers=None):
    """must be authorized to use v4 api, otherwise an HTTPError will be raised

    Arguments:
        json {dict}

        headers {dict}

    Returns:
        requests.Response
    """

    session = requests.session()

    request = requests.Request('POST', base_url, headers=headers, json=json)

    return session.send(session.prepare_request(request))