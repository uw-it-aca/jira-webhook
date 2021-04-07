# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.conf import settings
from django.views import View
from django.http import HttpResponse
from django.core.signing import BadSignature
from jira.exceptions import JIRAError
from jira_webhook.dao.jira import JiraClient
import hmac
import hashlib
import json


class APIView(View):
    def verify_signature(self, request):
        body = request.body.encode('utf-8')
        signature = request.META.get('HTTP_X_HUB_SIGNATURE', '')
        token = getattr(settings, 'GITHUB_TOKEN', '')

        h = hmac.new(token, body, hashlib.sha1)
        digest = 'sha1={}'.format(h.hexdigest())

        if digest != signature:
            raise BadSignature()

    def post(self, request, *args, **kwargs):
        try:
            self.verify_signature(request)
        except BadSignature as ex:
            return HttpResponse('{}'.format(ex), status=403)

        event_type = request.META.get('HTTP_X_GITHUB_EVENT', '')

        if event_type == 'push':
            try:
                data = json.loads(request.body)
            except Exception as ex:
                return HttpResponse('{}'.format(ex), status=400)

            client = JiraClient(
                host=getattr(settings, 'JIRA_HOST'),
                auth=(getattr(settings, 'JIRA_USER'),
                      getattr(settings, 'JIRA_PASS')))

            branch = data.get('ref')
            repository = data.get('repository').get('full_name')
            for commit in data.get('commits', []):
                try:
                    client.process_commit(commit, branch, repository)
                except JIRAError as ex:
                    if ex.status_code != 404:
                        return HttpResponse(
                            json.dumps({'url': ex.url, 'error': ex.text}),
                            status=ex.status_code)
                except Exception as ex:
                    return HttpResponse('{}'.format(ex), status=403)

        return HttpResponse(status=204)
