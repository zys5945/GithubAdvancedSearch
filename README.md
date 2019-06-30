# GithubUtility

This project aims to provide a python api for the github search API (both v3 and v4), while also adding extra functionalities.

## Example

The following piece of code retrieves all open issues with the label 'good first issue' and does not appear in the body of an open pull request, from pandas github repository:

```
from search import PrAndIssueSearch, cross_filter
from pprint import pprint

base_search = PrAndIssueSearch() \
.repo('pandas-dev/pandas')

issues = base_search.clone() \
.is_('open') \
.is_('issue') \
.label('good first issue') \
.execute()

all_open_prs = base_search.clone() \
.is_('open') \
.is_('pr') \
.fields("""
    ... on PullRequest{
        bodyText
    }
""") \
.execute()

def filter_fn(issue, prs, context, issues, issue_index):
    issue_number_string = str(issue['number'])

    for pr in prs:
        if issue_number_string in pr['fields']['bodyText']:
            return False

    return True

interested_issues = cross_filter(issues, all_open_prs, filter_fn)

interested_issue_numbers = list(map(lambda issue: issue['number'], interested_issues))

pprint(interested_issue_numbers)
```

For the specifics of the api, especially the graphql syntax, please visit github documentation.

https://developer.github.com/v3/

https://developer.github.com/v4/

## FAQ

### Where's the documentation?

Documentation for non-trivial methods can be found in the source code

### How to setup an oauth token?

Go to your github profile page -> Developer Settings -> Personal Access Tokens and click on "Generate new token".

You do not need to grant it any access if you are only searching for and within public repos.