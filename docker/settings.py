from .base_settings import *
import os

INSTALLED_APPS += [
    'jira_webhook.apps.JiraWebhookConfig',
]

GITHUB_WEBHOOK_SECRET = bytes(os.getenv('GITHUB_WEBHOOK_SECRET', ''),
                              encoding='utf8')
GITHUB_API_TOKEN = os.getenv('GITHUB_API_TOKEN')

JIRA_HOST = os.getenv('JIRA_HOST')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')

LOGGING['loggers'] = {
    '': {
        'handlers': ['stdout', 'stderr'],
        'level': 'DEBUG',
        'propagate': True,
    },
}
