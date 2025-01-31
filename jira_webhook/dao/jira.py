# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.conf import settings
from jira_webhook import UW_JIRA_BASE_URL
from jira import JIRA
import re

ISSUE_CAPTURE_RE = re.compile(r'([a-z]+-[0-9]+)', re.IGNORECASE)
NON_ISSUE_RE = re.compile(r'^(?:patch|pycodestyle)-', re.IGNORECASE)


class JiraClient(JIRA):
    UW_JIRA_BASE_URL = '{server}/{rest_path}/{rest_api_version}/{path}'

    def __init__(self, server=None, token=None):
        if server is None:
            server = getattr(settings, 'JIRA_HOST')

        if token is None:
            token = getattr(settings, 'JIRA_API_TOKEN')

        # options = {'headers': {'Accept': 'application/json,*/*;q=0.9'}}

        super(JiraClient, self).__init__(server=server, token_auth=token)

    def _get_url(self, path, base=''):
        base = UW_JIRA_BASE_URL
        options = self._options.copy()
        options.update({'path': path})
        return base.format(**options)

    def process_commit(self, commit, branch, repository):
        message = commit.get('message', '')
        for m in ISSUE_CAPTURE_RE.findall(message):
            if bool(NON_ISSUE_RE.match(m)):
                continue

            issue = self.issue(m)

            comment = self.add_comment(
                issue, 'Commit on branch {} ({}):\n{}'.format(
                    branch, repository, message))

            continue

            label = 'commit-{}'.format(branch)
            if label not in issue.fields.labels:
                issue.fields.labels.append(label)
                issue.update(fields={'labels': issue.fields.labels})
