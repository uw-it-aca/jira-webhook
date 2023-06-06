# Copyright 2023 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from jira_webhook import process_commit
from urllib3 import connection_from_url
import argparse
import json
import os

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

        token = getattr(settings, 'GITHUB_API_TOKEN')
        connection = connection_from_url('https://api.github.com')
        headers = {
            'User-Agent': 'Jira-WebHook Backfill 1.0',
            'Authorization': 'token {}'.format(token),
        }

        jira = JiraClient()

        for branch in BRANCHES:
            branch_name = 'refs/heads/{}'.format(branch)
            repository_full_name = '{}/{}'.format(org, repository)

            next_commits_url = '/repos/{}/{}/commits?sha={}'.format(
                org, repository, branch)

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
                print('Error: {}'.format(ex))
        return next_url
