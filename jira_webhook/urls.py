# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.urls import re_path
from jira_webhook.views import APIView

urlpatterns = [
    re_path(r'^api/v1/event$', APIView.as_view()),
]
