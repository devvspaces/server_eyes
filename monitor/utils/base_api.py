"""
Base api client abstract module
"""

from typing import List, Tuple
import requests
from requests import Response


class BaseAPIClient:
    """
    Base api client for basic api commands
    """

    def __init__(
        self, domain: str = None, endpoints: dict = None,
        headers: dict = None
    ) -> None:
        """
        Set request methods POST, PUT, PATCH, DELETE FUNCTIONS
        Initialize endpoints and headers
        """

        self.__request = {
            'post': requests.post,
            'put': requests.put,
            'patch': requests.patch,
            'delete': requests.delete,
            'get': requests.get,
        }

        if headers is None:
            headers = dict()

        self.__endpoints = endpoints
        self.__headers = headers
        self.__domain = domain

    def get_domain(self) -> dict:
        """
        Returns base url for the api
        """

        if self.__domain is not None:
            return self.__domain

        raise NotImplementedError('No base domain added')

    def get_endpoints(self) -> dict:
        """
        Returns endpoints added for api client
        """

        if self.__endpoints is not None:
            return self.__endpoints

        raise NotImplementedError('Endpoints dictionary is needed')

    def get_headers(self) -> dict:
        """
        Returns headers for api client
        """
        headers = self.__headers
        return headers

    def get_endpoint_url(self, endpoint: str) -> str:
        """
        Return Url for an endpoint

        Args:
            endpoint: key name for endpoint in endpoints
        """

        endpoints = self.get_endpoints()
        endpoint = endpoints.get(endpoint)
        if endpoint is None:
            raise ValueError('API endpoint does not exist')
        return endpoint

    def build_uri(self, endpoint: str, url_values: dict = None) -> str:
        """
        Return full url for an endpoint

        Args:
            url_values: to replace "-key-" in endpoint url
        """
        url = self.get_endpoint_url(endpoint)

        if url_values is not None:
            for key, val in url_values.items():
                url = url.replace(key, str(val))

        return f'{self.get_domain()}{url}'

    def get_method_func(self, method: str):
        """
        Get request function to use to make request
        """

        func = self.__request.get(method)
        if func is None:
            raise ValueError('Request method does not exist')
        return func

    def fetch_delete(
        self, endpoint: str, url_values: dict = None
    ) -> Tuple[bool, dict]:
        """
        Call delete request for api object
        """

        print('Called delete request', self, endpoint)

        url = self.build_uri(endpoint, url_values)
        method = self.get_method_func('delete')
        response: Response = method(url, headers=self.get_headers())

        return response.status_code, response.json()

    def fetch_post(
        self, method='post', endpoint='', data=None,
        url_values=None, files=None
    ) -> Tuple[int, dict]:
        """
        Call post on api for details provided
        """

        url = self.build_uri(endpoint, url_values)

        print(f'Called {method} request', self, endpoint)

        if data is None:
            data = dict()

        if files is None:
            files = dict()

        method = self.get_method_func(method)
        response: Response = method(
            url, json=data, headers=self.get_headers(), files=files)

        return response.status_code, response.json()

    def fetch_get(
        self, endpoint, params: dict = None, url_values: dict = None
    ) -> Tuple[int, dict]:
        """
        Call post on api for details provided
        """

        url = self.build_uri(endpoint, url_values)

        print('Called get request', self, endpoint)

        if params is None:
            params = dict()

        method = self.get_method_func('get')
        response: Response = method(
            url, params=params, headers=self.get_headers())

        return response.status_code, response.json()


class BaseAbstractDNS(BaseAPIClient):
    """
    Abstract class for domain name service apis
    """
    def __init__(self, endpoints, domain, headers):
        """
        Initializes the base api and other properties
        """
        super().__init__(
            endpoints=endpoints, domain=domain, headers=headers)

    def get_domains_list(self):
        """
        Get all domains connected to account
        """
        raise NotImplementedError

    def create_subdomain(self):
        """
        Create subdomain for provided domain
        """
        raise NotImplementedError

    def delete_subdomain(self):
        """
        Delete subdomain for provided domain
        """
        raise NotImplementedError

    def get_subdomains(self):
        """
        Returns all subdomains for provided domain
        """
        raise NotImplementedError

    def update_record(self):
        """
        Updates the record for the domain
        """
        raise NotImplementedError
