from client import UW_JIRA
from jira.exceptions import JIRAError
import hmac
import hashlib
import base64
import boto3
import json
import os
import re

JIRA_CLIENT = None
KMS_CLIENT = boto3.client('kms', region_name='us-west-2')
ISSUE_RE = re.compile(r'([a-z]+-[0-9]+)', re.IGNORECASE)


def get_jira_client():
    global JIRA_CLIENT
    if JIRA_CLIENT is None:
        if 'JIRA_PASSWORD_ENC' in os.environ:
            raw = base64.b64decode(os.environ['JIRA_PASSWORD_ENC'])
            password = KMS_CLIENT.decrypt(CiphertextBlob=raw)['Plaintext']
        elif 'JIRA_PASSWORD' in os.environ:
            password = os.environ.get('JIRA_PASSWORD')
        else:
            raise Exception('Missing JIRA credentials')

        host = os.environ.get('JIRA_HOST')
        user = os.environ.get('JIRA_USER')

        JIRA_CLIENT = UW_JIRA(host=host, auth=(user, password))

    return JIRA_CLIENT


def validate_signature(event):
    body = event.get('body', '').encode('utf-8')
    signature = event.get('headers', {}).get('X-Hub-Signature')

    raw = base64.b64decode(os.environ['GITHUB_SECRET_ENC'])
    token = KMS_CLIENT.decrypt(CiphertextBlob=raw)['Plaintext']

    h = hmac.new(token, body, hashlib.sha1)
    digest = 'sha1={}'.format(h.hexdigest())
    if digest != signature:
        raise Exception('Invalid signature: {} {}'.format(digest, signature))


def process_commit(commit, branch, repository):
    message = commit.get('message', '')
    for match in ISSUE_RE.findall(message):
        jira = get_jira_client()
        issue = jira.issue(match)

        comment = jira.add_comment(
            issue, 'Commit on branch {} ({}):\n{}'.format(
                branch, repository, message))

        label = 'commit-{}'.format(branch)
        if label not in issue.fields.labels:
            issue.fields.labels.append(label)
            issue.update(fields={'labels': issue.fields.labels})


def response(status=200, body={}):
    return {'statusCode': status, 'body': json.dumps(body)}


def main(event, *args, **kwargs):
    try:
        validate_signature(event)
    except Exception as ex:
        return response(status=403, body={'error': str(ex)})

    event_type = event.get('headers', {}).get('X-GitHub-Event', '')

    if event_type == 'push':
        body = json.loads(event.get('body'))
        branch = body.get('ref')
        repository = body.get('repository').get('full_name')

        for commit in body.get('commits', []):
            try:
                process_commit(commit, branch, repository)
            except JIRAError as ex:
                return response(status=ex.status_code,
                                body={'url': ex.url, 'error': ex.text})
            except Exception as ex:
                return response(status=403, body={'error': str(ex)})

    return response()


if __name__ == '__main__':
    main()
