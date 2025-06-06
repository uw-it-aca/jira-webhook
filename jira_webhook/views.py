# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.conf import settings
from django.views import View
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from jira.exceptions import JIRAError
from jira_webhook.dao.jira import JiraClient
from logging import getLogger
import hmac
import hashlib
import json

logger = getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class APIView(View):
    def verify_signature(self, request):
        signature = request.META.get('HTTP_X_HUB_SIGNATURE_256')
        if signature is None:
            return False

        h = hmac.new(getattr(settings, 'GITHUB_WEBHOOK_SECRET', ''),
                     msg=request.body,
                     digestmod=hashlib.sha256)
        digest = 'sha256={}'.format(h.hexdigest())

        return hmac.compare_digest(digest, signature)

    def post(self, request, *args, **kwargs):
        # Verify message signature
        if not self.verify_signature(request):
            return HttpResponse('Invalid signature', status=403)

        # Verify event type
        if request.META.get('HTTP_X_GITHUB_EVENT', '') != 'push':
            return HttpResponse(status=204)

        try:
            data = json.loads(request.body)
        except Exception as ex:
            logger.error(f'Error loading request.body: {ex}; {request.body}')
            return HttpResponse('{}'.format(ex), status=400)

        jira = JiraClient()

        branch = data.get('ref')
        repository = data.get('repository').get('full_name')
        for commit in data.get('commits', []):
            try:
                jira.process_commit(commit, branch, repository)
            except JIRAError as ex:
                if ex.status_code != 404:
                    return HttpResponse(
                        json.dumps({'url': ex.url, 'error': ex.text}),
                        status=ex.status_code)
            except Exception as ex:
                return HttpResponse('{}'.format(ex), status=403)

        return HttpResponse(status=204)
