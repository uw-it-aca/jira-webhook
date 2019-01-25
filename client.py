from jira import JIRA
from requests import Session
from bs4 import BeautifulSoup
from urllib.parse import urljoin


class UW_JIRA(JIRA):
    """A Jira client with a saml session to handle authn on an SSO redirect"""
    def __init__(self, host='', auth=(None, None)):
        """Initialize with the basic auth so we use our _session."""
        self._session = UwSamlSession(credentials=auth)
        super(UW_JIRA, self).__init__(host, basic_auth=('ignored', 'haha'))

    def _create_http_basic_session(self, *basic_auth, timeout=None):
        """Hide the JIRA implementation so it uses our instance of_session."""


class UwSamlSession(Session):
    """A requests.Session that checks responses for IdP redirects."""
    def __init__(self, credentials=(None, None),
                 idp='https://idp.u.washington.edu/'):
        self._credentials = credentials
        self._idp = idp
        super(UwSamlSession, self).__init__()

    def request(self, method, url, *args, **kwargs):
        """
        For every request that comes in, submit the request and check if we
        got redirected to the IdP for authentication. If so, submit the
        configured credentials and post back to the SP for completion of the
        request.
        """
        request = super(UwSamlSession, self).request
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
