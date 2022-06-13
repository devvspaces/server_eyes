"""
Process module test
"""


import json
from django.test import SimpleTestCase
from utils.process import ServerProcess, NoServerClient
from utils.paramiko_wrapper import Dir
from utils.general import cryptor


class ServerProcessTest(SimpleTestCase):
    def setUp(self) -> None:
        self.process = ServerProcess(
            host='127.0.0.1',
            username='main',
            password=cryptor.encrypt('test1234'),
            web_server='apache'
        )

    def test_get_client(self):
        with self.assertRaises(NoServerClient):
            self.process.get_client()

    def test_get_username(self):
        self.assertEqual(self.process.get_username(), 'main')

    def test_get_host(self):
        self.assertEqual(self.process.get_host(), '127.0.0.1')

    def test_get_home_directory(self):
        self.assertEqual(self.process.get_home_directory(), '/home/main')

    def test_create_new_dir(self):
        computed = self.process.create_new_dir()
        self.assertEqual(str(computed), '/home/main')
        self.assertEqual(computed.__class__, Dir)

    def test_get_base_directory(self):
        self.assertEqual(
            self.process.get_base_directory(), '/home/main/ServerMonitor')

    def test_get_list_dir_command(self):
        computed = self.process.get_list_dir_command('/a/b/c')
        self.assertEqual(computed, 'ls -la /a/b/c')

    def test_get_projects_directory(self):
        self.assertEqual(
            self.process.get_projects_directory(),
            '/home/main/ServerMonitor/deploys/projects')

    def test_get_temp_dir(self):
        self.assertEqual(
            self.process.get_temp_dir(), '/home/main/ServerMonitor/temp')

    def test_temp_file_path(self):
        computed = self.process.temp_file_path()
        computed = computed.replace('/home/main/ServerMonitor/temp', '')
        self.assertTrue(computed.startswith('/'))
        self.assertTrue(len(computed) >= 30)

    def test_need_sudo(self):
        computed = self.process.need_sudo('/etc/super/duh')
        self.assertTrue(computed)
        computed = self.process.need_sudo('/home/main/test1/test12')
        self.assertFalse(computed)

    def test_get_directory_filenames(self):
        with open('utils/tests/test_ls.txt', 'r') as file:
            text = file.read()

        computed = self.process.get_directory_filenames(text)
        expected = ['.gitignore', 'README.md', 'requirements.txt']
        self.assertListEqual(computed, expected)

    def test_parse_website_data(self):
        other_logs = [
            {
                'name': 'ErrorLog',
                'location': '/var/www/error.log',
            },
        ]
        other_logs = json.dumps(other_logs)
        data = {
            'file_name': '/etc/nginx/sites-available/project-rolodex.conf',
            'error_log': '/home/nmae/that/down.log',
            'access_log': '/home/nmae/that/up.log',
            'other_logs': other_logs,
            'urls': ['23.23.23.23', 'www.coming.com', 'dating.com'],
        }
        expected = {
            'name': 'Project Rolodex',
            'conf_filename': 'project-rolodex.conf',
            'conf_filepath': data['file_name'],
            'error_log': '/home/nmae/that/down.log',
            'access_log': '/home/nmae/that/up.log',
            'other_logs': other_logs,
            'urls': ['23.23.23.23', 'www.coming.com', 'dating.com'],
        }

        computed = self.process.parse_website_data(data)
        self.assertDictEqual(expected, computed)
