# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.conf import settings
from jira import JIRA
from logging import getLogger
import re

logger = getLogger(__name__)

ISSUE_CAPTURE_RE = re.compile(r'([a-z]+-[0-9]+)', re.IGNORECASE)
NON_ISSUE_RE = re.compile(r'^(?:patch|pycodestyle)-', re.IGNORECASE)


class JiraClient():
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = JIRA(
                server=getattr(settings, 'JIRA_HOST'),
                token_auth=getattr(settings, 'JIRA_API_TOKEN'))
        return self._client

    def process_commit(self, commit, branch, repository):
        message = commit.get('message', '')
        for m in ISSUE_CAPTURE_RE.findall(message):
            if bool(NON_ISSUE_RE.match(m)):
                continue

            issue = self.client.issue(m)

            comment = self.client.add_comment(
                issue, f'Commit on branch {branch} ({repository}):\n{message}')

            logger.info(f'Added comment to {m}: {message}')

            continue

            label = f'commit-{branch}'
            if label not in issue.fields.labels:
                issue.fields.labels.append(label)
                issue.update(fields={'labels': issue.fields.labels})
