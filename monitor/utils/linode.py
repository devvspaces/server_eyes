"""
Linode api client wrapper
"""

from typing import List
from django.conf import settings
from .base_api import BaseAPIClient


class LinodeClient(BaseAPIClient):
    """
    Wrapper for linode api
    """
    def __init__(self):
        """
        Initializes the base api and other properties
        """

        # Set the linode api version here
        domain = f"https://api.linode.com/{self.get_linode_version()}/"

        # Define endpoints
        domains = 'domains'
        endpoints = {
            'domains_list': f'{domains}',
            'domain_records': f'{domains}/-domainId-/records',
            'record_update': f'{domains}/-domainId-/records/-recordId-',
        }

        # Add the personal access token gotten from linode here
        self.__personal_access_token = settings.LINODE_PAT
        headers = {
            'Authorization': f'Bearer {self.__personal_access_token}',
        }

        super().__init__(endpoints=endpoints, domain=domain, headers=headers)

    def get_linode_version(self) -> str:
        """
        Return the version for the linode api
        """
        return settings.LINODE_API_VERSION

    def get_domains_list(self) -> List[dict]:
        """
        Get all domains connected to account
        """

        status, data = self.fetch_get('domains_list')

        if status == 200:
            return data[data]

    def create_subdomain(self, data: dict, domain_id):
        """
        Create subdomain for provided domain

        Args:
            Domain is the An instance of the main domain
        """

        status, data = self.fetch_post(
            endpoint='domain_records',
            data=data, url_values={'-domainId-': domain_id})
        status = status == 200
        return status, data

    def is_A_record(self, record: dict):
        """
        Checks if a record is of Type 'A'
        """

        record_type = record.get('type')
        return record_type == 'A'

    def parse_subdomains(self, records: list):
        """
        Returns a list of only subdomains
        """

        return [record for record in records if self.is_A_record(record)]

    def get_subdomains(self, domain_id):
        """
        Returns all subdomains for provided domain

        Args:
            Domain is the An instance of the main domain
        """

        status, data = self.fetch_get(
            'domain_records', url_values={'-domainId-': domain_id})
        status = status == 200

        if status is False:
            return []

        all_records = data['data']
        subdomains = self.parse_subdomains(all_records)

        return subdomains

    def update_record(self, data, domain_id, record_id):
        """
        Updates the record for the domain
        """

        url_values = {
            '-domainId-': domain_id,
            '-recordId-': record_id,
        }

        status, result = self.fetch_post(
            method='put', endpoint='record_update',
            data=data, url_values=url_values)

        status = status == 200

        return status, result


# NOTE: Linode client will be initialize per account
# Account -> many linode domains
linodeClient = LinodeClient()
