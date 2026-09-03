# Copyright 2026 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.core.management.base import BaseCommand

from jira_webhook.dao.jira import JiraClient


class Command(BaseCommand):
    help = ('Assigns issues that have been fixed, but not assigned to'
            'someone else')

    def add_arguments(self, parser):
        parser.add_argument('project')
        parser.add_argument('assignee')

    def handle(self, *args, **options):
        project = options.get('project')
        assignee = options.get('assignee')

        jira = JiraClient()

        issues = jira.client.search_issues((
            f'project = {project} AND status = Resolved and resolution in (Fixed, '
            f'Completed) and (assignee != {assignee} OR assignee IS EMPTY) and '
            f'updated < -15minute'
        ), expand='changelog', maxResults=1000)

        for issue in issues:
            has_assignee_change = False
            has_resolution = False
            changelog = issue.changelog
            changelog.histories.reverse()

            for history in changelog.histories:
                for item in history.items:
                    if item.field == 'assignee':
                        if not has_resolution:
                            has_assignee_change = True
                    elif item.field == 'status':
                        has_resolution = True

            if not has_assignee_change:
                jira.client.add_comment(issue, f'Auto assigning issue to {assignee}')
                jira.client.assign_issue(issue, assignee)
