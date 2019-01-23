from utils import get_jira_client
import json
import re

ISSUE_RE = re.compile(r'([a-z]+-[0-9]+)', re.IGNORECASE)


def main(*args, **kwargs):
    branch = None
    repository = None
    commits = []

    jira = get_jira_client()

    for commit in commits:
        message = commit['message']

        for match in ISSUE_RE.findall(message):
            issue = jira.issue(match)

            jira.add_comment(issue, 'Commit on branch: {} ({})'.format(
                branch, repository))
            issue.fields.labels.append('commit-{}'.format(branch))
            issue.update(fields={'labels': issue.fields.labels})


if __name__ == '__main__':
    main()
