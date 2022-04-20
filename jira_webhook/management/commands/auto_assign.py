# Copyright 2022 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from django.core.management.base import BaseCommand, CommandError
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

        issues = jira.search_issues((
            'project = {} AND status = Resolved and resolution in (Fixed, '
            'Completed) and (assignee != {} OR assignee IS EMPTY) and '
            'updated < -15minute').format(project, assignee),
            expand='changelog', maxResults=1000)

        for issue in issues:
            has_assignee_change = False
            has_resolution = False
            changelog = issue.changelog
            changelog.histories.reverse()
            resolution_date = None

            for history in changelog.histories:
                for item in history.items:
                    if item.field == 'assignee':
                        if not has_resolution:
                            has_assignee_change = True
                    elif item.field == 'status':
                        has_resolution = True

            if not has_assignee_change:
                jira.add_comment(
                    issue, 'Auto assigning issue to {}'.format(assignee))
                jira.assign_issue(issue, assignee)
