from .base_settings import *
import os

INSTALLED_APPS += [
    'jira_webhook.apps.JiraWebhookConfig',
]

GITHUB_WEBHOOK_SECRET = bytes(os.getenv('GITHUB_WEBHOOK_SECRET', ''),
                              encoding='utf8')
GITHUB_API_TOKEN = os.getenv('GITHUB_API_TOKEN')

JIRA_HOST = os.getenv('JIRA_HOST')
JIRA_USER = os.getenv('JIRA_USER')
JIRA_PASS = os.getenv('JIRA_PASS')
