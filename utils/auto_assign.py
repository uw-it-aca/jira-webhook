from jira_webhook import get_jira_client
import argparse


def auto_assign(project, assignee):
    """
    Automatically assigns issues that have been fixed, but not assigned to
    someone else
    """
    jira = get_jira_client()

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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('project')
    parser.add_argument('assignee')
    args = parser.parse_args()
    auto_assign(args.project, args.assignee)
