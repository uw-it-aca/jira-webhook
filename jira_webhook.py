from jira.client import JIRA
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

            host = os.environ.get('JIRA_HOST', None)
            user = os.environ.get('JIRA_USER', None)

            JIRA_CLIENT = JIRA(server=host, basic_auth=(user, password))
        else:
            raise Exception('Missing Jira credentials')

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


def main(event, *args, **kwargs):
    try:
        validate_signature(event)
    except Exception as ex:
        return {'statusCode': 403, 'body': 'Error: {}'.format(ex)}

    event_type = event.get('headers', {}).get('X-GitHub-Event', '')

    if event_type == 'push':
        body = json.loads(event.get('body'))
        branch = body.get('ref')
        repository = body.get('repository').get('full_name')

        try:
            jira = get_jira_client()
        except Exception as ex:
            return {'statusCode': 403, 'body': 'Error: {}'.format(ex)}

        for commit in body.get('commits', []):
            message = commit['message']

            for match in ISSUE_RE.findall(message):
                issue = jira.issue(match)

                jira.add_comment(issue, 'Commit on branch: {} ({})'.format(
                    branch, repository))
                issue.fields.labels.append('commit-{}'.format(branch))
                issue.update(fields={'labels': issue.fields.labels})

    return {'statusCode': 200, 'body': 'OK'}


if __name__ == '__main__':
    main()
