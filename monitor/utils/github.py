"""
Github api client wrapper
"""

import hashlib
import hmac
from typing import Dict, List

from django.conf import settings
from django.urls import reverse

from utils.logger import err_logger, logger  # noqa

from .base_api import BaseAPIClient
from .general import cryptor


class GithubClient(BaseAPIClient):
    """
    Wrapper class for api
    """

    def __init__(self, password: str = ''):
        """
        Setup properties and headers
        """
        super().__init__()

        # Add the personal access token gotten from github here
        # Set the github api version here

        # Decrypt password
        self.__personal_access_token = cryptor.decrypt(password)
        headers = {
            'Authorization': f'Token {self.__personal_access_token}',
            "Accept": self.get_accept_header(),
        }

        domain = "https://api.github.com"

        endpoints = {
            'orgs': '/user/orgs',
            'repos': '/-type-/-owner-/repos',
            'create-webhook': '/repos/-owner-/-repo-/hooks',
            'delete-webhook': '/repos/-owner-/-repo-/hooks/-hook_id-',
            'branches': '/repos/-owner-/-repo-/branches',
            'user': '/user',
        }

        super().__init__(endpoints=endpoints, domain=domain, headers=headers)

    def get_github_version(self) -> str:
        """
        Return the version for the gihtub api
        """

        return settings.GITHUB_API_VERSION

    def get_accept_header(self):
        """
        Get the accept value to place in header
        """

        return f"application/vnd.github.v{self.get_github_version()}+json"

    def get_organizations_names(self) -> list:
        """
        Get the organization names that user belongs to
        """
        status, organizations = self.fetch_get('orgs')

        if status == 200:
            # Get names all oranizations
            organization_names = [org['login'] for org in organizations]

            return organization_names

        return []

    def get_repository_list(
        self, owner: str, owner_type: str
    ) -> List[Dict[str, str]]:
        repository_list = []

        # Set url_values for user account
        url_values = {
            '-type-': owner_type,
            '-owner-': owner
        }

        status, result = self.fetch_get('repos', url_values=url_values)

        if status == 200:
            for repo in result:
                branches_url = repo['branches_url'].rstrip('{/branch}')
                name = repo['name']
                full_name = repo['full_name']
                id = repo['id']
                clone_url = repo['clone_url']
                private: bool = repo['private']
                default_branch = repo['default_branch']

                data = {
                    'repo_id': id,
                    'name': name,
                    'full_name': full_name,
                    'clone_url': clone_url,
                    'branches_url': branches_url,
                    'private': private,
                    'default_branch': default_branch
                }

                repository_list.append(data)

        return repository_list

    def get_repository_branches(self, owner: str, repo: str) -> str:
        """
        Returns braches of a repository
        """

        branches = []
        url_values = {
            '-owner-': owner,
            '-repo-': repo,
        }

        status, result = self.fetch_get('branches', url_values=url_values)

        if status == 200:
            branches = [branch['name'] for branch in result]

        return branches

    def create_repository_webhook(
        self, owner: str, name: str, domain: str, secret: str
    ) -> int:
        """
        Create webhook for github repository
        """

        web_path = reverse('panel:github-webhook')
        url = f'https://{domain}{web_path}'

        data = {
            'events': [
                'push',
            ],
            'config': {
                'url': url,
                'content_type': 'json',
                'secret': secret
            }
        }

        url_values = {
            '-repo-': name,
            '-owner-': owner
        }

        status, result = self.fetch_post(
            endpoint='create-webhook', url_values=url_values, data=data)

        if status == 201:
            hook_id = result['id']
            return hook_id

    def delete_repository_webhook(
        self, owner: str, repo: str, hook_id: int
    ) -> bool:
        """
        Delete github repository webhook
        """

        # Set url_values for user account
        url_values = {
            '-repo-': repo,
            '-owner-': owner,
            '-hook_id-': hook_id,
        }

        status = self.fetch_delete(
            endpoint='delete-webhook', url_values=url_values)

        return status == 204

    def validate_github_account(self) -> bool:
        """
        Validate user account
        """

        status, _ = self.fetch_get('user')

        if status == 200:
            return True

        elif status != 401:
            logger.info(f'''Validate githhub account
            Returned status error code - {status}''')

        return False

    @staticmethod
    def validate_payload(body: bytes, secret: str, signature: str):
        """
        Validate SHA256 github webhook payload
        """

        hmac3 = hmac.new(key=secret.encode(), digestmod=hashlib.sha256)
        hmac3.update(bytes(body.decode(), encoding="utf-8"))
        value = hmac3.hexdigest()
        value = 'sha256=' + value
        return hmac.compare_digest(value, signature)
