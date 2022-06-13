"""
Class for deploy and other
ssh services
"""


import json
import logging
import os
from typing import Dict, Tuple
from uuid import uuid4

from django.conf import settings
from django.utils.safestring import SafeString, mark_safe
from django.utils.text import slugify

from utils.general import cryptor, get_in_dict_format, get_name_from_text
from utils.paramiko_wrapper import Dir, ExcecuteError, SshClient
from utils.webservers import create_web_server


class NoServerClient(Exception):
    """
    Exception for no server client
    """


class NoAppLogger(Exception):
    """
    Exception for no logger for app
    """


class EmptyFilePath(Exception):
    """
    Exception for empty file path
    """


class ServerProcess:
    def __init__(
        self, host: str, username: str, password: str, web_server: str
    ) -> None:
        self.__host = host
        self.__username = username
        self.__password = cryptor.decrypt(password)
        self.__port = 22

        self.client: SshClient = None

        self.web_server = create_web_server(web_server, self.get_host())

        self.__server_details = None

    def create_client(self):
        """
        Connect and create new server ssh client
        """

        if self.client is None:
            self.client = SshClient(
                self.get_host(), self.__port,
                self.get_username(), self.__password)

    def destroy(self):
        """
        Kills the client connection and delete client
        """

        client = getattr(self, 'client', None)
        if client is not None:
            self.client.close()
            self.client = None

    def __del__(self):
        self.destroy()

    def get_client(self) -> SshClient:
        """
        Get server client

        :raises NoServerClient: Server is not connected
        :return: SSH client for this process
        :rtype: SshClient
        """

        if self.client is None:
            raise NoServerClient

        return self.client

    def get_username(self):
        """
        Get server username used to login
        """

        return self.__username

    def get_host(self):
        """
        Get server host used to connect
        """

        return self.__host

    def get_home_directory(self) -> str:
        """
        Get server home directory

        :return: path
        :rtype: str
        """
        if self.get_username() != 'root':
            return f"/home/{self.get_username()}"

        return "/root"

    def create_new_dir(self):
        """
        Create new dir, default location to server home directory
        """

        dir_obj = Dir(self.__username)
        dir_obj.cd(self.get_home_directory())
        return dir_obj

    def clean_server_details(self, details: Dict[str, str]):
        for key, value in details.items():
            details[key] = value.strip('\"')
        return details

    def add_server_details(self):
        """
        Get server details from client server
        and add it to object
        """

        command = "egrep '^(VERSION|NAME|HOME_URL)=' /etc/os-release"
        stdout: str = self.get_client().execute(command, sudo=True)
        details = get_in_dict_format(stdout)
        self.clean_server_details(details)
        self.__server_details = details

    def get_server_details(self):
        """
        Get the connected server details
        """

        if self.__server_details is None:
            self.add_server_details()

        return self.__server_details

    def get_server_name(self):
        """
        Get the server os name
        """

        return self.get_server_details().get('NAME')

    def get_server_version(self):
        """
        Get the server os version
        """

        return self.get_server_details().get('VERSION')

    def get_server_os_home_url(self):
        """
        Get the server os home url
        """

        return self.get_server_details().get('HOME_URL')

    def get_active_state(self, service_name: str):
        """
        Get the status of a running service
        """

        command = f"systemctl show {service_name} --no-page"
        stdout = self.get_client().execute(command, sudo=True)

        value = get_name_from_text('ActiveState', stdout)
        return value == 'active'

    def get_base_directory(self) -> str:
        """
        Get the directory to place all files created

        :return: path
        :rtype: str
        """

        return self.get_home_directory() + '/ServerMonitor'

    def get_temp_dir(self) -> str:
        """
        Get the directory to place temporary files

        :return: path
        :rtype: str
        """

        return self.get_base_directory() + '/temp'

    def temp_file_path(self) -> str:
        uid = str(uuid4())
        temp_file_path = self.get_temp_dir() + f"/{uid}"
        return temp_file_path

    def need_sudo(self, path: str) -> bool:
        return not str(path).startswith(self.get_home_directory())

    def get_move_file_command(self, from_path: str, to_path: str) -> str:
        return f"mv {from_path} {to_path}"

    def move_file(self, from_path: str, to_path: str) -> bool:
        command = self.get_move_file_command(from_path, to_path)
        require_sudo = self.need_sudo(from_path) or self.need_sudo(to_path)
        self.get_client().execute(command, sudo=require_sudo)
        return True

    def get_copy_file_command(self, from_path: str, to_path: str) -> str:
        return f"cp {from_path} {to_path}"

    def copy_file(self, from_path: str, to_path: str) -> bool:
        command = self.get_copy_file_command(from_path, to_path)
        require_sudo = self.need_sudo(from_path) or self.need_sudo(to_path)
        self.get_client().execute(command, sudo=require_sudo)
        return True

    def get_read_file_command(self, file_path: str) -> str:
        if not file_path:
            raise EmptyFilePath
        return f"cat {file_path}"

    def read_file(self, file_path: str):
        """
        Read file content from server
        """

        command = self.get_read_file_command(file_path)
        use_sudo = self.need_sudo(file_path)
        stdout: str = self.get_client().execute(command, sudo=use_sudo)
        return stdout

    def __write_content(self, file_path: str, content: str):
        ftp = self.get_client().client.open_sftp()
        file = ftp.file(file_path, "w", -1)
        file.write(content)
        file.flush()
        ftp.close()

    def write_file(self, file_path: str, content: str):
        if self.need_sudo(file_path):
            temp_path = self.temp_file_path()
            self.__write_content(temp_path, content)
            self.move_file(temp_path, file_path)
        else:
            self.__write_content(file_path, content)

    def get_log_content(self, log_path: str) -> SafeString:
        """
        Get read log from server
        """

        log_text = self.read_file(log_path)

        if log_text.strip():
            log_text = log_text.replace('\n', '<br><br>')
            return mark_safe(log_text)

        return 'No Logs'

    def get_service_logs(self, name: str) -> SafeString:
        """Get journalctl logs for a service

        :return: Mark Safe text
        :rtype: django.utils.safestring.marksafe
        """

        command = f'journalctl -u {name} --no-page'
        logs: str = self.get_client().execute(command, sudo=True)
        logs = logs.replace('\n', '<br><br>')
        return mark_safe(logs)

    def get_list_dir_command(self, path: str) -> str:
        return f"ls -la {path}"

    def get_directory_filenames(self, text: str) -> str:
        files = text.strip().splitlines()[1:]
        clean_files = []
        for file in files:
            if not file.startswith('d'):
                file_name = file.split()[-1]
                clean_files.append(file_name)
        return clean_files

    def list_directory_files(self, path: str) -> list:
        command = self.get_list_dir_command(path)
        stdout = self.get_client().execute(command)
        return self.get_directory_filenames(stdout)

    def fetch_enabled_sites(self) -> list:
        web_enabled_path = self.web_server.get_enabled_path()
        dir_obj = self.create_new_dir()
        dir_obj.cd(web_enabled_path)
        file_names = self.list_directory_files(dir_obj)
        results_list = []
        file_names = self.web_server.clean_conf_filenames(file_names)
        for file_name in file_names:
            dir_obj.cd(file_name)
            stdout = self.read_file(dir_obj)
            details = self.web_server.get_site_details(stdout)
            details['file_name'] = file_name
            results_list.append(details)
            dir_obj.go_back()

        return results_list

    def get_projects_directory(self) -> str:
        """
        Get the directory to place all clone
        repositories (projects code base directory)

        :return: projects directory path
        :rtype: str
        """
        return self.get_base_directory() + '/deploys/projects'

    def parse_website_data(self, data: Dict[str, str]) -> dict:
        """
        Parse out the data from dictionary for website
        instance update

        :param data: Data gotten from get_enabled_sites
        :type data: Dict[str, str]
        :return: Cleaned and parsed data
        :rtype: dict
        """

        conf_name = data['file_name'].split('/')[-1]
        name = conf_name.split('.')[0]
        name = slugify(name).replace('-', ' ').title()
        parsed_data = {
            'name': name,
            'conf_filename': conf_name,
            'conf_filepath': data['file_name'],
            'access_log': data['access_log'],
            'error_log': data['error_log'],
            'other_logs': data['other_logs'],
            'urls': data['urls']
        }

        return parsed_data


class AppProcess(ServerProcess):
    def __init__(
        self, name: str, clone_url: str,
        branch: str, url: str, *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.__name = name
        self.logger = self.create_logger()
        self.dir = self.create_new_dir()
        self.clone_url = clone_url
        self.branch = branch
        self.url = url

    def get_app_name(self) -> str:
        return self.__name

    def destroy(self):
        """
        Delete logger and client
        """

        logger = getattr(self, 'logger', None)
        if logger is not None:
            del self.logger
            self.logger = None

        super().destroy()

    def get_log_directory_path(self) -> str:
        """
        Get deploy log directory

        :return: Log directory path for app
        :rtype: str
        """
        return f"{settings.BASE_DIR}/logs/deployed_apps/{self.get_app_name()}"

    def get_log_file(self) -> str:
        """
        Get deploy log file path

        :return: Log file path for app
        :rtype: str
        """
        return f"{self.get_log_directory_path()}/deploy.log"

    def create_logger(self) -> logging.Logger:
        """
        Returns a newly created logger
        """
        logger = logging.getLogger(self.get_app_name() + str(uuid4()))
        logger.setLevel(logging.INFO)
        log_file = self.get_log_file()
        try:
            handler = logging.FileHandler(filename=log_file, mode='a')
        except FileNotFoundError:
            os.makedirs(self.get_log_directory_path())
            handler = logging.FileHandler(filename=log_file, mode='a')
        format = logging.Formatter(
            fmt="{levelname} : {asctime} : {message}", style="{")
        handler.setFormatter(format)
        logger.addHandler(handler)
        return logger

    def get_logger(self) -> logging.Logger:
        if self.logger is not None:
            return self.logger
        raise NoAppLogger

    def get_project_directory(self) -> str:
        """
        Get the directory to clone
        app project repository (project code base directory)

        :return: app project directory path
        :rtype: str
        """
        return f"{self.get_projects_directory()}/{self.get_app_name()}"

    def cd_project_directory(self):
        self.dir.cd(self.get_project_directory())

    def create_project_directory(self):
        command = f"mkdir -p {self.get_project_directory()}"
        self.get_client().execute(command)

    def git_clone(self):
        logger = self.get_logger()
        self.cd_project_directory()
        clone_command = f"git clone {self.clone_url} {self.dir}"
        stdout, stderr, status = self.get_client().execute(
            clone_command, raise_exception=False)
        if status != 0:
            if stderr.find('already exists and is not an empty directory') != -1:  # noqa
                logger.info("Clone Output: Repository already cloned moving to checkout")  # noqa
            else:
                raise ExcecuteError(
                    stdout=stdout, stderr=stderr, status=status)

        logger.info('Cloning repository success')

    def git_checkout(self):
        """
        Set branch to selected branch: If branch
        not there leave at default master branch
        """

        logger = self.get_logger()
        self.cd_project_directory()
        command = f"cd {self.dir};git checkout {self.branch}"
        stdout = self.get_client().execute(command)
        logger.info(f"\nCheckout Output: {stdout}\n")
        logger.info('Checkout repository success')

    def git_pull(self):
        """
        Run git pull to update branch

        :raises ExcecuteError: command was not successful
        """

        logger = self.get_logger()
        self.cd_project_directory()
        command = f"cd {self.dir};git pull {self.clone_url} {self.branch}"
        self.get_client().execute(command)
        logger.info('Git pull update on branch successfully')

    def get_project_root_dir(self):
        return self.get_project_directory() + '/build'

    def configure_server(self) -> Tuple[str, str]:
        logger = self.get_logger()
        conf_details = self.web_server.get_configuration_html(
            name=self.get_app_name(),
            url=self.url,
            root_dir=self.get_project_root_dir(),
        )
        template = conf_details['template']
        access_log = conf_details['access_log']
        error_log = conf_details['error_log']

        # TODO: Remove this after test complete
        logger.info(f"{self.web_server} Template Output:\n{template}\n\n")

        conf_path = self.web_server.get_file_available_path(
            self.get_app_name())
        self.write_file(conf_path, template)
        logger.info(f"{self.web_server} configuration complete")
        return access_log, error_log

    def enable_web_server(self):
        """
        Enable web server configuration
        """

        logger = self.get_logger()
        app = self.get_app_name()
        enabled_path = self.web_server.get_file_enabled_path(app)
        file_exists = self.get_client().file_exists(enabled_path)

        if file_exists:
            logger.info(
                'Project configuration already enabled')
        else:
            command = self.web_server.get_enable_command(app)
            self.get_client().execute(command, sudo=True)
            logger.info(
                'Project configuration successfully enabled')

    def restart_web_server(self):
        command = self.web_server.get_restart_command()
        self.get_client().execute(command, sudo=True)
        self.get_logger().info(
            f'{self.web_server} restart completed')


class ReactProcess(AppProcess):
    def get_project_root_dir(self):
        return self.get_project_directory() + '/build'

    def npm_install(self):
        logger = self.get_logger()
        self.cd_project_directory()
        command = f"cd {self.dir};npm install"
        stdout = self.get_client().execute(command)
        logger.info(f"Npm install Output: {stdout}")
        logger.info('Project dependencies installed successfully')

    def add_homepage(self, url: str):
        logger = self.get_logger()
        self.cd_project_directory()
        package_path = f"{self.dir}/package.json"
        stdout = self.read_file(package_path)
        package_json: dict = json.loads(stdout)
        hompage = package_json.get('homepage')
        if (hompage is None) or (hompage != url):
            package_json['homepage'] = url
            content = json.dumps(package_json, indent=2)
            self.write_file(package_path, content)
            logger.info('Package.json homepage updated')
        else:
            logger.info('Package.json homepage already added')

    def npm_build(self):
        logger = self.get_logger()
        self.cd_project_directory()
        command = f"cd {self.dir};npm run build"
        stdout = self.get_client().execute(command)
        logger.info(f"Npm Build Output: {stdout}")
        logger.info('Project build is completed')
