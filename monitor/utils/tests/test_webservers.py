"""
Webservers module test
"""

import json

from django.test import SimpleTestCase
from utils.webservers import (Apache, BaseWebserver, Nginx,
                              WebserverDoesNotExist, create_web_server)


class BaseWebserverTest(SimpleTestCase):
    def setUp(self) -> None:
        self.init = {
            'enabled_path': '/etc/fake/sites-enabled',
            'available_path': '/etc/fake/sites-available',
            'log': '/var/log/fake',
            'access_name': 'access_log',
            'error_name': 'error_log',
            'conf_server_name': 'server_name',
            'version': '4.0.2',
            'ip_address': '127.0.0.1',
        }
        self.webserver = BaseWebserver(**self.init)

    def test_create_web_server_apache(self):
        """
        Test create_web_server for apache server
        """

        computed = create_web_server('apache', ip_address='127.0.0.1')
        self.assertEqual(computed.__class__, Apache)
        self.assertEqual(computed.get_host_ip_address(), '127.0.0.1')

    def test_create_web_server_nginx(self):
        """
        Test create_web_server for nginx server
        """

        computed = create_web_server('nginx', ip_address='127.0.0.1')
        self.assertEqual(computed.__class__, Nginx)
        self.assertEqual(computed.get_host_ip_address(), '127.0.0.1')

    def test_create_web_server_error(self):
        """
        Test create_web_server for not existing web server
        """

        with self.assertRaises(WebserverDoesNotExist):
            create_web_server('gunicorn', ip_address='127.0.0.1')

    def read_test_file_one(self):
        """
        Read test file one

        :return: return content of test file one
        :rtype: str
        """
        with open('utils/tests/webserver_test_1.txt', 'r') as file:
            return file.read()

    def test_basic_get_functions(self):
        """
        Test basic get functions on class
        """

        computed = self.webserver.get_version()
        self.assertEqual(computed, self.init['version'])

        computed = self.webserver.get_host_ip_address()
        self.assertEqual(computed, self.init['ip_address'])

        computed = self.webserver.get_log_path()
        self.assertEqual(computed, self.init['log'])

        computed = self.webserver.get_enabled_path()
        self.assertEqual(computed, self.init['enabled_path'])

        computed = self.webserver.get_available_path()
        self.assertEqual(computed, self.init['available_path'])

        computed = self.webserver.get_access_log()
        self.assertEqual(computed, '/access.log')

        computed = self.webserver.get_access_name()
        self.assertEqual(computed, self.init['access_name'])

        computed = self.webserver.get_error_log()
        self.assertEqual(computed, '/error.log')

        computed = self.webserver.get_error_name()
        self.assertEqual(computed, self.init['error_name'])

        computed = self.webserver.get_conf_server_name()
        self.assertEqual(computed, self.init['conf_server_name'])

    def test_get_full_access_log(self):
        """
        Test get_full_access_log
        """

        computed = self.webserver.get_full_access_log()
        expected = self.init['log'] + '/access.log'
        self.assertEqual(computed, expected)

    def test_get_file_available_path(self):
        """
        Test get_file_available_path
        """

        computed = self.webserver.get_file_available_path('first')
        expected = self.init['available_path'] + '/first.conf'
        self.assertEqual(computed, expected)

    def test_get_file_enabled_path(self):
        """
        Test get_file_enabled_path
        """

        computed = self.webserver.get_file_enabled_path('first')
        expected = self.init['enabled_path'] + '/first.conf'
        self.assertEqual(computed, expected)

    def test_get_full_error_log(self):
        """
        Test get_full_error_log
        """

        computed = self.webserver.get_full_error_log()
        expected = self.init['log'] + '/error.log'
        self.assertEqual(computed, expected)

    def test_get_default_logs(self):
        """
        Test get_default_logs
        """

        computed = self.webserver.get_default_logs()
        error = self.init['log'] + '/error.log'
        access = self.init['log'] + '/access.log'
        self.assertEqual(computed['access'], access)
        self.assertEqual(computed['error'], error)

    def test_non_implemented_methods(self):
        """
        Test for non implemented methods
        """

        with self.assertRaises(NotImplementedError):
            self.webserver.get_configuration_html()
            self.webserver.get_configuration_php()
            self.webserver.get_configuration_python()
            self.webserver.get_enable_command()

    def test_clean_conf_filenames(self):
        """
        Test for clean_conf_filenames
        """

        filenames = ['a', 2, 'c']
        computed = self.webserver.clean_conf_filenames(filenames)
        self.assertEqual(filenames, computed)

    def test_get_conf_log_name(self):
        """
        Test get_conf_log_name
        """

        test_file = self.read_test_file_one()
        computed = self.webserver.get_conf_log_name('errorLog', test_file)
        self.assertEqual(computed, '/var/www/Error.log')

        computed = self.webserver.get_conf_log_name('CustomLog', test_file)
        self.assertEqual(computed, '/cust/other/one/demo.log')

    def test_get_conf_access(self):
        """
        Test get_conf_access
        """

        test_file = self.read_test_file_one()
        computed = self.webserver.get_conf_access(test_file)
        self.assertEqual(computed, '/home/nmae/that/up.log')

    def test_get_conf_error(self):
        """
        Test get_conf_error
        """

        test_file = self.read_test_file_one()
        computed = self.webserver.get_conf_error(test_file)
        self.assertEqual(computed, '/home/nmae/that/down.log')

    def get_test_get_conf_urls_expected(self):
        """
        Return expected result for 'Test get_conf_urls'

        :return: expected result
        :rtype: list
        """
        return ['23.23.23.23', 'www.coming.com', 'dating.com']

    def test_get_conf_urls(self):
        """
        Test get_conf_urls
        """

        test_file = self.read_test_file_one()
        computed = self.webserver.get_conf_urls(test_file)
        expected = self.get_test_get_conf_urls_expected()
        self.assertEqual(computed, expected)

    def get_test_get_all_logs_expected(self):
        """
        Return expected result for 'Test get_all_logs'

        :return: expected result
        :rtype: dict
        """

        expected_other_logs = [
            {
                'name': 'ErrorLog',
                'location': '/var/www/error.log',
            },
            {
                'name': 'errorLog',
                'location': '/var/www/Error.log',
            },
            {
                'name': 'AccessLog',
                'location': '/var/www/confirm/access.log',
            },
            {
                'name': 'AccessLog',
                'location': '/var/other/one/access.log',
            },
            {
                'name': 'AccessLog',
                'location': '/mainerror/other/one/access.log',
            },
            {
                'name': 'CustomLog',
                'location': '/cust/other/one/demo.log',
            },
            {
                'name': 'access_log',
                'location': '/spool/logs/nginx-access.log',
            },
        ]
        expected_other_logs = json.dumps(expected_other_logs)
        expected = {
            'error_log': '/home/nmae/that/down.log',
            'access_log': '/home/nmae/that/up.log',
            'other_logs': expected_other_logs
        }
        return expected

    def test_get_all_logs(self):
        """
        Test get_all_logs
        """

        test_file = self.read_test_file_one()
        computed = self.webserver.get_all_logs(test_file)
        expected = self.get_test_get_all_logs_expected()
        self.assertEqual(computed['error_log'], expected['error_log'])
        self.assertEqual(computed['access_log'], expected['access_log'])
        self.assertEqual(computed['other_logs'], expected['other_logs'])

    def test_get_site_details(self):
        """
        Test get_site_details
        """

        test_file = self.read_test_file_one()
        computed = self.webserver.get_site_details(test_file)
        expected = self.get_test_get_all_logs_expected()
        expected['urls'] = self.get_test_get_conf_urls_expected()
        self.assertEqual(computed['error_log'], expected['error_log'])
        self.assertEqual(computed['access_log'], expected['access_log'])
        self.assertEqual(computed['other_logs'], expected['other_logs'])
        self.assertEqual(computed['urls'], expected['urls'])

    def test_new_conf_access_error_log_paths(self):
        """
        Test for new_conf_access_error_log_paths
        """

        computed1, computed2 = self.webserver\
            .new_conf_access_error_log_paths('king')
        expected1 = '/var/log/fake/king.log'
        expected2 = '/var/log/fake/king.error.log'
        self.assertEqual(computed1, expected1)
        self.assertEqual(computed2, expected2)


class NginxTest(SimpleTestCase):
    def setUp(self) -> None:
        self.init = {
            'version': '4.0.2',
            'ip_address': '127.0.0.1',
        }
        self.webserver = Nginx(**self.init)

    def test_get_enable_command(self):
        """
        Test for get_enable_command
        """

        computed = self.webserver.get_enable_command('first')
        expected = 'ln -s /etc/nginx/sites-available/first.conf /etc/nginx/sites-enabled'  # noqa
        self.assertEqual(computed, expected)

    def test_get_restart_command(self):
        """
        Test for get_restart_command
        """

        computed = self.webserver.get_restart_command()
        self.assertEqual(computed, 'systemctl restart nginx')

    def test_get_configuration_html(self):
        """
        Test get_configuration_html
        """

        root_dir = '/home/king/kill/jump/website'
        name = 'king_portfolio'
        url = 'www.king.port.io'
        computed = self.webserver.get_configuration_html(
            root_dir=root_dir,
            name=name,
            url=url
        )

        access_log = '/var/log/nginx/king_portfolio.log'
        error_log = '/var/log/nginx/king_portfolio.error.log'

        template = """
            server {
                listen 80;
                listen [::]:80;


                root -root_dir-;
                index index.html index.htm index.nginx-debian.html;

                access_log -access_log- combined;
                error_log -error_log-;

                server_name -url-;


                location / {
                        try_files $uri $uri/ =404;
                }
            }
        """

        template = template.replace('-root_dir-', root_dir)
        template = template.replace('-access_log-', access_log)
        template = template.replace('-error_log-', error_log)
        template = template.replace('-url-', url)

        expected = {
            'template': template,
            'access_log': access_log,
            'error_log': error_log,
        }

        self.assertEqual(computed, expected)


class ApacheTest(SimpleTestCase):
    def setUp(self) -> None:
        self.init = {
            'version': '4.0.2',
            'ip_address': '127.0.0.1',
        }
        self.webserver = Apache(**self.init)

    def test_get_restart_command(self):
        """
        Test for get_restart_command
        """

        computed = self.webserver.get_restart_command()
        self.assertEqual(computed, 'systemctl restart apache2')

    def test_get_enable_command(self):
        """
        Test for get_enable_command
        """

        computed = self.webserver.get_enable_command('first')
        expected = 'a2ensite first.conf'
        self.assertEqual(computed, expected)

    def test_get_site_details(self):
        """
        Test apache get site details
        """

        with open('utils/tests/apache_test.txt', 'r') as file:
            test_file = file.read()
        expected_other_logs = [
            {
                'name': 'CustomLog',
                'location': '/var/log/apache2/demo.log',
            },
        ]
        expected_other_logs = json.dumps(expected_other_logs)
        expected = {
            'error_log': '/var/log/apache2/site.error.log',
            'access_log': '/var/www/confirm/site.log',
            'other_logs': expected_other_logs
        }
        expected['urls'] = ['23.23.23.23', 'www.coming.com', 'dating.com']

        computed = self.webserver.get_site_details(test_file)
        self.assertEqual(computed['error_log'], expected['error_log'])
        self.assertEqual(computed['access_log'], expected['access_log'])
        self.assertEqual(computed['other_logs'], expected['other_logs'])
        self.assertEqual(computed['urls'], expected['urls'])

    def test_clean_conf_filenames(self):
        """
        Test clean_conf_filenames
        """

        file_names = [
            'file1.conf',
            'file14.conf',
            'file1-le-ssl.conf',
            'file2.conf',
            'file14-le-ssl.conf',
            'file2-le-ssl.conf',
            'file45.conf',
        ]
        expected = ['file1.conf', 'file14.conf', 'file2.conf', 'file45.conf']
        computed = self.webserver.clean_conf_filenames(file_names)
        self.assertEqual(computed, expected)

    def test_get_configuration_html(self):
        """
        Test get_configuration_html
        """

        root_dir = '/home/miown/kill/jump/website'
        name = 'myportfolio'
        url = 'www.superme.port.io'
        access_log = '/var/log/apache2/myportfolio.log'
        error_log = '/var/log/apache2/myportfolio.error.log'
        template = f"""
        <VirtualHost *:80>
            ServerAdmin admin@{url}
            ServerName {url}

            "DocumentRoot {root_dir}
            DirectoryIndex index.html

            <Directory {root_dir}>
                Options Indexes FollowSymLinks MultiViews
                AllowOverride All
                Require all granted
            </Directory>

            ErrorLog {error_log}
            CustomLog {access_log} combined

        </VirtualHost>
        """

        expected = {
            'template': template,
            'access_log': access_log,
            'error_log': error_log,
        }

        computed = self.webserver.get_configuration_html(
            root_dir=root_dir,
            name=name,
            url=url
        )

        self.assertEqual(computed, expected)
