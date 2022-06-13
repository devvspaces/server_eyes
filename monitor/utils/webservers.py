"""
Module for web servers
"""


import json
import re
from typing import Dict, List, Tuple, Union


class WebserverDoesNotExist(Exception):
    """
    Exception that web server does not exist
    """


class BaseWebserver:
    """
    Base web server abstract class
    """
    def __init__(
        self, version: str = None,
        enabled_path: str = None,
        available_path: str = None,
        log: str = None,
        access_path: str = '/access.log',
        access_name: str = None,
        error_path: str = '/error.log',
        error_name: str = None,
        conf_server_name: str = None,
        ip_address: str = None
    ) -> None:
        """
        Creating new web server

        :param version: version of the web server, defaults to None
        :type version: str, optional
        :param enabled_path: path where enabled sites are
        kept, defaults to None
        :type enabled_path: str, optional
        :param available_path: path where available to
        be hosted kept, defaults to None
        :type available_path: str, optional
        :param log: path where default logs are stored, defaults to None
        :type log: str, optional
        :param access_path: default path for access log,
        defaults to '/access.log'
        :type access_path: str, optional
        :param access_name: default directive name for
        access log, defaults to None
        :type access_name: str, optional
        :param error_path: default path for error log,
        defaults to '/error.log'
        :type error_path: str, optional
        :param error_name: default directive name for
        error log, defaults to None
        :type error_name: str, optional
        :param conf_server_name: default directive name for
        web server hostnames, defaults to None
        :type conf_server_name: str, optional
        :param ip_address: ip address for cloud service hosting
        web server, defaults to None
        :type ip_address: str, optional
        """
        self.__version = version
        self.__enabled_path = enabled_path
        self.__log = log
        self.__access_path = access_path
        self.__access_name = access_name
        self.__error_path = error_path
        self.__error_name = error_name
        self.__conf_server_name = conf_server_name
        self.__ip_address = ip_address
        self.__available_path = available_path

    def get_version(self) -> str:
        """
        Get web server version

        :return: web server version
        :rtype: str
        """
        return self.__version

    def get_host_ip_address(self) -> str:
        """
        Get web server cloud service host ip address

        :return: host ip address for cloud service
        :rtype: str
        """

        return self.__ip_address

    def get_log_path(self) -> str:
        """
        Get default log path for web server

        :return: _description_
        :rtype: str
        """

        return self.__log

    def get_enabled_path(self) -> str:
        """
        Get default enabled site path for web server

        :return: _description_
        :rtype: str
        """

        return self.__enabled_path

    def get_available_path(self) -> str:
        return self.__available_path

    def get_file_available_path(self, name: str) -> str:
        return self.get_available_path() + f'/{name}.conf'

    def get_file_enabled_path(self, name: str) -> str:
        return self.get_enabled_path() + f'/{name}.conf'

    def get_access_log(self) -> str:
        return self.__access_path

    def get_access_name(self) -> str:
        return self.__access_name

    def get_error_log(self) -> str:
        return self.__error_path

    def get_error_name(self) -> str:
        return self.__error_name

    def get_conf_server_name(self) -> str:
        return self.__conf_server_name

    def get_full_access_log(self) -> str:
        return self.get_log_path() + self.__access_path

    def get_full_error_log(self) -> str:
        return self.get_log_path() + self.__error_path

    def get_default_logs(self) -> Dict[str, str]:
        logs = {
            'access': self.get_full_access_log(),
            'error': self.get_full_error_log(),
        }
        return logs

    def get_configuration_html(self, *args, **kwargs):
        raise NotImplementedError

    def get_configuration_php(self, *args, **kwargs):
        raise NotImplementedError

    def get_configuration_python(self, *args, **kwargs):
        raise NotImplementedError

    def get_enable_command(self, *args, **kwargs):
        raise NotImplementedError

    def get_restart_command(self, *args, **kwargs):
        raise NotImplementedError

    def clean_conf_filenames(self, file_names: list):
        return file_names

    def get_conf_log_name(self, log_name: str, text: str) -> str:
        search = log_name + r' (/.+\.log)'
        pattern = re.compile(search)
        result = pattern.search(text)

        log_path = ''

        if result:
            log_path = result.group(1)

        return log_path

    def get_conf_access(self, text: str) -> str:
        access_log_name = self.get_conf_log_name(self.get_access_name(), text)
        if not access_log_name:
            access_log_name = self.get_full_access_log()
        return access_log_name

    def get_conf_error(self, text: str) -> str:
        error_log_name = self.get_conf_log_name(self.get_error_name(), text)
        if not error_log_name:
            error_log_name = self.get_full_error_log()
        return error_log_name

    def get_conf_urls(self, text: str) -> list:
        search = self.get_conf_server_name() + r'\s(.*)'
        pattern = re.compile(search)
        result = pattern.findall(text)
        cleaned_links = []
        default_link = self.get_host_ip_address()
        if result:
            urls_ips = result[0].split(' ')
            for _link in urls_ips:
                _link = _link.rstrip(';')
                clean_link = _link if _link != '_' else default_link
                cleaned_links.append(clean_link)
        return cleaned_links

    def get_all_logs(self, conf: str) -> Dict[str, str]:
        access_log_name = self.get_conf_access(conf)
        error_log_name = self.get_conf_error(conf)

        all_logs: List[str] = re.findall(r'\w+ /.+\.log', conf)
        other_logs = []
        for item in all_logs:
            try:
                key, value = item.split(' ')

                if (error_log_name == value) or (access_log_name == value):
                    continue

                log_dict = {
                    'name': key,
                    'location': value,
                }
                other_logs.append(log_dict)

            except ValueError:
                pass
        other_logs = json.dumps(other_logs)

        logs = {
            'error_log': error_log_name,
            'access_log': access_log_name,
            'other_logs': other_logs
        }

        return logs

    def get_site_details(self, conf: str) -> Dict[str, str]:
        links = self.get_conf_urls(conf)
        all_logs = self.get_all_logs(conf)
        data = {
            'urls': links,
        }
        data.update(all_logs)

        return data

    def new_conf_access_error_log_paths(self, name: str) -> Tuple[str, str]:
        error_log = self.get_log_path() + f"/{name}.error.log"
        access_log = self.get_log_path() + f"/{name}.log"
        return access_log, error_log


class Nginx(BaseWebserver):
    def __init__(self, version: str = None, ip_address: str = None) -> None:
        init_data = {
            'enabled_path': '/etc/nginx/sites-enabled',
            'available_path': '/etc/nginx/sites-available',
            'log': '/var/log/nginx',
            'access_name': 'access_log',
            'error_name': 'error_log',
            'conf_server_name': 'server_name',
            'version': version,
            'ip_address': ip_address,
        }
        super().__init__(**init_data)

    def get_enable_command(self, name: str):
        available_path = self.get_file_available_path(name)
        return f"ln -s {available_path} {self.get_enabled_path()}"

    def get_restart_command(self) -> str:
        return "systemctl restart nginx"

    def get_configuration_html(
        self, name: str, url: str, root_dir: str
    ) -> Dict[str, str]:
        """
        Get web server configuration for deploying new website
        basic html websites

        :param name: Name for website apache log
        :type name: str
        :param url: Website url
        :type url: str
        :param root_dir: website root directory
        :type root_dir: str
        :return: configuration text for website
        :rtype: _type_
        """

        access_log, error_log = self.new_conf_access_error_log_paths(name)
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

        return {
            'template': template,
            'access_log': access_log,
            'error_log': error_log,
        }

    def __str__(self) -> str:
        """
        Return web server name

        :return: Return web server name
        :rtype: str
        """

        return 'Nginx Web Server'


class Apache(BaseWebserver):
    def __init__(self, version: str = '2', ip_address: str = None) -> None:
        init_data = {
            'enabled_path': '/etc/apache2/sites-enabled',
            'available_path': '/etc/apache2/sites-available',
            'log': '/var/log/apache2',
            'access_name': 'AccessLog',
            'error_name': 'ErrorLog',
            'conf_server_name': 'ServerName',
            'version': version,
            'ip_address': ip_address
        }
        super().__init__(**init_data)

    def get_site_details(self, conf: str) -> Dict[str, str]:
        conf = conf.replace('${APACHE_LOG_DIR}', self.get_log_path())
        return super().get_site_details(conf)

    def get_restart_command(self) -> str:
        return "systemctl restart apache2"

    def get_enable_command(self, name: str):
        return f"a2ensite {name}.conf"

    def get_configuration_html(
        self, name: str, url: str, root_dir: str
    ) -> Dict[str, str]:
        """
        Get web server configuration for deploying new website
        basic html websites

        :param name: Name for website apache log
        :type name: str
        :param url: Website url
        :type url: str
        :param root_dir: website root directory
        :type root_dir: str
        :return: configuration text for website
        :rtype: _type_
        """

        access_log, error_log = self.new_conf_access_error_log_paths(name)
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
        return {
            'template': template,
            'access_log': access_log,
            'error_log': error_log,
        }

    def clean_conf_filenames(self, file_names: list) -> list:
        return list(filter(lambda x: 'le-ssl' not in x, file_names))

    def __str__(self) -> str:
        """
        Return web server name

        :return: Return web server name
        :rtype: str
        """

        return 'Apache Web Server'


def create_web_server(
    name: str, ip_address: str = None
) -> Union[Nginx, Apache]:
    web_servers = {
        'apache': Apache,
        'nginx': Nginx,
    }

    server_class: Union[Nginx, Apache] = web_servers.get(name)
    if server_class is not None:
        return server_class(ip_address=ip_address)

    raise WebserverDoesNotExist
