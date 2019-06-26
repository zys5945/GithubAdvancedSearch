import gql
import gql.transport.requests as gql_requests
import datetime
import time
from urllib.parse import urljoin

base_url = "https://api.github.com/graphql"

def send(data, headers=None, json=None):
    """must be authorized to use v4 api
    Arguments:
        data {str}
    
    Returns:
        object
    """

    gql_client = gql.Client(
        transport=gql_requests.RequestsHTTPTransport(
            url=base_url,
            headers=headers,
            use_json=True,
        )
    )

    return gql_client.execute(gql.gql(data))