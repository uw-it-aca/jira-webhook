# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.conf import settings
from jira import JIRA
from requests import Session
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

ISSUE_CAPTURE_RE = re.compile(r'([a-z]+-[0-9]+)', re.IGNORECASE)
NON_ISSUE_RE = re.compile(r'^(?:patch|pycodestyle)-', re.IGNORECASE)


class JiraClient(JIRA):
    UW_JIRA_BASE_URL = '{server}/{rest_path}/{rest_api_version}/{path}'

    def __init__(self, server=None, auth=None):
        if server is None:
            server = getattr(settings, 'JIRA_HOST')

        if auth is None:
            auth = (getattr(settings, 'JIRA_USER'),
                    getattr(settings, 'JIRA_PASS'))

        super(JiraClient, self).__init__(server=server, basic_auth=auth)

    def _get_url(self, path, base=''):
        base = UW_JIRA_BASE_URL
        options = self._options.copy()
        options.update({"path": path})
        return base.format(**options)

    # def _create_http_basic_session(self, *basic_auth, timeout=None):
    #    """Hide the JIRA implementation so it uses our instance of_session."""

    def process_commit(self, commit, branch, repository):
        message = commit.get('message', '')
        for match in ISSUE_CAPTURE_RE.findall(message):
            if bool(NON_ISSUE_RE.match(match)):
                continue

            issue = self.issue(match)

            comment = self.add_comment(
                issue, 'Commit on branch {} ({}):\n{}'.format(
                    branch, repository, message))

            label = 'commit-{}'.format(branch)
            if label not in issue.fields.labels:
                issue.fields.labels.append(label)
                issue.update(fields={'labels': issue.fields.labels})


class SamlSession(Session):
    """A requests.Session that checks responses for IdP redirects."""
    def __init__(self, credentials=(None, None)):
        self._credentials = credentials
        self._idp = getattr(settings, 'IDP_HOST', '')
        super(SamlSession, self).__init__()

    def request(self, method, url, *args, **kwargs):
        """
        For every request that comes in, submit the request and check if we
        got redirected to the IdP for authentication. If so, submit the
        configured credentials and post back to the SP for completion of the
        request.
        """
        request = super(SamlSession, self).request
        response = request(method, url, *args, **kwargs)
        for _ in range(2):
            if not response.url.startswith(self._idp):
                break
            url, form = self._form_data(response.content)
            if 'j_username' in form:
                user, password = self._credentials
                form.update({
                    'j_username': user,
                    'j_password': password})
            # don't let the client override content-type
            headers = {'Content-Type': None}
            response = request('POST', url=url, data=form, headers=headers)
            if response.status_code != 200:
                raise Exception('saml login failed', response)
        return response

    def _form_data(self, content):
        """Return a tuple of (form url, form data) from response content."""
        bs = BeautifulSoup(content, 'html.parser')
        form = bs.find('form')
        url = urljoin(self._idp, form['action'])
        data = {element['name']: element.get('value')
                for element in form.find_all('input')
                if element.get('name')}
        return url, data
