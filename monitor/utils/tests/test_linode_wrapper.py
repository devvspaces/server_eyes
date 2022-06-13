"""
Linode api wrapper client test
"""
from django.conf import settings
from django.test import SimpleTestCase
from utils.linode import LinodeClient


class LinodeClientTest(SimpleTestCase):

    def setUp(self) -> None:
        """
        Set up test for client
        """

        self.linode = LinodeClient()

    def test_get_linode_version(self):
        """
        Test get_linode_version
        """

        version = self.linode.get_linode_version()
        self.assertEqual(settings.LINODE_API_VERSION, version)

    def test_headers(self):
        """
        Test is headers are accurate
        """

        computed = self.linode.get_headers()

        computed2 = list(computed.keys()).index('Authorization')
        self.assertNotEqual(computed2, -1)

    def test_is_A_record(self):
        """
        Test is_A_record
        """

        record = {
            'type': 'A'
        }
        self.assertTrue(self.linode.is_A_record(record))

        record = {
            'type': 'AAAA'
        }
        self.assertFalse(self.linode.is_A_record(record))

        record = {
            'type': 'MX'
        }
        self.assertFalse(self.linode.is_A_record(record))

    def test_parse_subdomains(self):
        """
        Test parse_subdomains
        """

        records = [
            {
                'type': 'A'
            },
            {
                'type': 'AAAA'
            },
            {
                'type': 'MX'
            }
        ]

        expected1 = [
            {
                'type': 'A'
            }
        ]

        computed = self.linode.parse_subdomains(records)
        self.assertEqual(expected1, computed)
        self.assertEqual(1, len(computed))
        self.assertEqual('A', computed[0]['type'])
