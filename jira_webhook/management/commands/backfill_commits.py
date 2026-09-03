# Copyright 2026 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

import json

from django.conf import settings
from django.core.management.base import BaseCommand
from urllib3 import connection_from_url

from jira_webhook.dao.jira import JiraClient

BRANCHES = ['develop', 'qa', 'master', 'main']


class Command(BaseCommand):
    help = ('Gets commit messages mentioning issues before the webhook'
            'was installed, for a given repository')

    def add_arguments(self, parser):
        parser.add_argument('org')
        parser.add_argument('repository')

    def handle(self, *args, **options):
        org = options.get('org')
        repository = options.get('repository')

        connection = connection_from_url('https://api.github.com')
        headers = {
            'User-Agent': 'Jira-WebHook Backfill 1.0',
            'Authorization': f'token {settings.GITHUB_API_TOKEN}',
        }

        jira = JiraClient()

        for branch in BRANCHES:
            branch_name = f'refs/heads/{branch}'
            repository_full_name = '{org}/{repository}'

            next_commits_url = f'/repos/{org}/{repository}/commits?sha={branch}'

            while next_commits_url:
                response = connection.urlopen(
                    'GET', next_commits_url, headers=headers)

                next_commits_url = self._get_next_url(response)

                commits = json.loads(response.data)
                for commit in commits:
                    jira.process_commit(
                        commit, branch_name, repository_full_name)

    def _get_next_url(self, response):
        next_url = None
        for link in response.getheader('link', '').split(','):
            try:
                (url, rel) = link.split(';')
                if 'next' in rel:
                    next_url = url.lstrip('<').rstrip('>')
            except KeyError:
                pass
            except Exception as ex:
                print(f'Error: {ex}')
        return next_url
