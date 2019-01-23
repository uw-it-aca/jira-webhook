from jira.client import JIRA
import base64
import boto3
import os

JIRA_CLIENT = None


def get_jira_client():
    global JIRA_CLIENT
    if JIRA_CLIENT is None:
        if 'JIRA_PASSWORD_ENC' in os.environ:
            raw = base64.b64decode(os.environ['JIRA_PASSWORD_ENC'])

            kms_client = boto3.client('kms', region_name='us-west-2')
            password = kms_client.decrypt(CiphertextBlob=raw)['Plaintext']

            host = os.environ.get('JIRA_HOST', None)
            user = os.environ.get('JIRA_USER', None)

            JIRA_CLIENT = JIRA(server=host, basic_auth=(user, password))
        else:
            raise Exception('Missing Jira credentials')

    return JIRA_CLIENT
