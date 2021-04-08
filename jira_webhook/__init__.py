# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from jira.resources import Resource

Resource.JIRA_BASE_URL = '{server}/{rest_path}/{rest_api_version}/{path}'
