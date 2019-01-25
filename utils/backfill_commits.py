from jira_webhook import process_commit
from urllib3 import connection_from_url
import argparse
import json
import os

BRANCHES = ['develop', 'qa', 'master']


def get_next_url(response):
    next_url = None
    for link in response.getheader('link', '').split(','):
        try:
            (url, rel) = link.split(';')
            if 'next' in rel:
                next_url = url.lstrip('<').rstrip('>')
        except KeyError:
            pass
        except Exception as ex:
            print('Error: {}'.format(ex))
    return next_url


def backfill_commits(org, repository):
    """
    Gets commit messages mentioning issues before the webhook was installed,
    for a given repository
    """
    connection = connection_from_url('https://api.github.com')
    headers = {
        'User-Agent': 'Jira-WebHook Backfill 1.0',
        'Authorization': 'token {}'.format(os.environ.get('GITHUB_TOKEN')),
    }

    for branch in BRANCHES:
        branch_name = 'refs/heads/{}'.format(branch)
        repository_full_name = '{}/{}'.format(org, repository)

        next_commits_url = '/repos/{}/{}/commits?sha={}'.format(
            org, repository, branch)

        while next_commits_url:
            response = connection.urlopen(
                'GET', next_commits_url, headers=headers)

            next_commits_url = get_next_url(response)

            commits = json.loads(response.data)
            for commit in commits:
                process_commit(commit, branch_name, repository_full_name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('org')
    parser.add_argument('repository')
    args = parser.parse_args()
    backfill_commits(args.project, args.assignee)
