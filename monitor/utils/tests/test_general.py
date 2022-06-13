"""
Test for all functions and classes in
utils/general.py
"""


from django.test import SimpleTestCase
from utils.general import get_in_dict_format, get_name_from_text


class SimpleTest(SimpleTestCase):
    def setUp(self) -> None:
        pass

    def test_get_name_from_text(self):
        """
        Test for get name from text
        """

        with open('utils/tests/get_name_from_text_str.txt', 'r') as file:
            text = file.read()

        value = get_name_from_text('ConditionResult', text)
        self.assertEqual(value, 'no')

        value = get_name_from_text('ActiveState', text)
        self.assertEqual(value, 'inactive')

    def test_get_in_dict_format(self):
        """
        Test get_in_dict_format
        """

        text = """
        NAME=king
        VERSION=2.3.4 Ubuntu(45.67)
        SAMPLE=like my code
        """

        value = get_in_dict_format(text)
        expected = {
            'NAME': 'king',
            'VERSION': '2.3.4 Ubuntu(45.67)',
            'SAMPLE': 'like my code',
        }
        self.assertEqual(value, expected)
