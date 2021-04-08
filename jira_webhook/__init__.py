# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from jira.resources import Resource
from jira.client import JIRA

UW_JIRA_BASE_URL = '{server}/{rest_path}/{rest_api_version}/{path}'

"""
Patch for Resource and JIRA classes to force the UW Jira API url format.
"""
# def _get_uw_url(self, path):
#    options = self._options.copy()
#    options.update({'path': path})
#    return UW_JIRA_BASE_URL.format(**options)
# Resource._get_url = _get_uw_url
#

Resource.JIRA_BASE_URL = UW_JIRA_BASE_URL
JIRA.JIRA_BASE_URL = UW_JIRA_BASE_URL
