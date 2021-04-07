from .base_settings import *
import os

INSTALLED_APPS += [
    'jira_webhook.apps.JiraWebhookConfig',
]

IDP_HOST = 'https://idp.u.washington.edu/'
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
JIRA_HOST = os.getenv('JIRA_HOST')
JIRA_USER = os.getenv('JIRA_USER')
JIRA_PASS = os.getenv('JIRA_PASS')
