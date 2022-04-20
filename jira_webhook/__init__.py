# Copyright 2022 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from jira.resources import Resource

UW_JIRA_BASE_URL = '{server}/{rest_path}/{rest_api_version}/{path}'


"""
Patch the Resource._get_url method to force the UW Jira API url format.
"""


def _get_uw_url(self, path):
    options = self._options.copy()
    options.update({'path': path})
    return UW_JIRA_BASE_URL.format(**options)


Resource._get_url = _get_uw_url
