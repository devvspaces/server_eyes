"""
Python test for base api client
"""
import requests
from django.test import SimpleTestCase
from utils.base_api import BaseAPIClient


class BaseApiTest(SimpleTestCase):

    def setUp(self) -> None:
        """
        Set up BaseAPIClient for testing
        """

        self.api_client = BaseAPIClient()

        self.endpoints = {
            'api_test1': '/domains',
            'api_test2': '/domains/-domainId-/records',
            'api_test3': '/domains/-domainId-',
            'api_test4': '/-domainId-',
        }
        self.domain = 'http://test'

        self.api_client2 = BaseAPIClient(
            endpoints=self.endpoints,
            domain=self.domain
        )

    def test_init(self):
        """
        Test is base client init properties
        are corrent
        """

        with self.assertRaises(NotImplementedError):
            self.api_client.get_domain()
            self.api_client.get_endpoints()

    def test_get_domain(self):
        """
        Test get_domain function
        """

        self.assertEqual(self.api_client2.get_domain(), self.domain)

    def test_get_headers(self):
        """
        Test get_headers function
        """

        self.assertEqual(self.api_client2.get_headers(), dict())

    def test_get_endpoints(self):
        """
        Test get_endpoints function
        """

        self.assertEqual(self.api_client2.get_endpoints(), self.endpoints)

    def test_get_endpoint_url(self):
        """
        Test get_endpoint_url function
        """

        self.assertEqual(
            self.api_client2.get_endpoint_url('api_test1'),
            self.endpoints.get('api_test1'))

    def test_build_uri(self):
        """
        Test build_uri function
        """

        url = self.api_client2.build_uri('api_test1')
        expected_url = self.domain + self.endpoints.get('api_test1')
        self.assertEqual(url, expected_url)

        url_values = {
            '-domainId-': 'user'
        }
        url = self.api_client2.build_uri('api_test2', url_values)
        expected_url = self.domain + "/domains/user/records"
        self.assertEqual(url, expected_url)

        url = self.api_client2.build_uri('api_test3', url_values)
        expected_url = self.domain + "/domains/user"
        self.assertEqual(url, expected_url)

        url = self.api_client2.build_uri('api_test4', url_values)
        expected_url = self.domain + "/user"
        self.assertEqual(url, expected_url)

    def test_get_method_func(self):
        """
        Test get_method_func
        """

        with self.assertRaises(ValueError):
            self.api_client2.get_method_func('empty')

        for name in ['post', 'get', 'delete', 'put', 'patch']:
            self.assertIn(
                self.api_client2.get_method_func(name).__name__,
                requests.__dict__)
