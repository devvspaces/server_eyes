from typing import Type

from django.db import models
from django.utils.text import slugify
from utils.general import cryptor
from utils.model_mixins import ModelChangeFunc
from utils.process import AppProcess, ReactProcess, ServerProcess
from utils.validators import validate_special_char


class BaseApp(ModelChangeFunc):
    STATUS = (
        ('inactive', 'Inactive',),
        ('pending', 'Pending',),
        ('deployed', 'Deployed',),
        ('failed', 'Failed',),
        ('disabled', 'Disabled',),
        # ('maintenance', 'Maintenance',),
    )

    # App type
    app_type = None

    # Server (apps can only be deployed on a server)
    server = models.ForeignKey('panel.Server', on_delete=models.CASCADE)

    # Project fields
    project_name = models.CharField(
        max_length=255, validators=[validate_special_char], unique=True)
    slug = models.SlugField(max_length=512, unique=True, blank=True)
    project_dir = models.CharField(max_length=255)
    conf_dir = models.CharField(max_length=255)
    access_log = models.CharField(max_length=255)
    error_log = models.CharField(max_length=255)

    # Repository
    repository = models.ForeignKey(
        'panel.Repository', on_delete=models.CASCADE)
    branch = models.CharField(
        max_length=50, help_text='Branch on repository to deploy,\
 this checkouts to default master branch if not specified')

    # Domain
    domain = models.ForeignKey(
        'panel.Domain', on_delete=models.DO_NOTHING, null=True)
    subdomain = models.ForeignKey(
        'panel.Subdomain', on_delete=models.DO_NOTHING, null=True)

    # Status
    status = models.CharField(
        choices=STATUS, default='inactive', max_length=255)

    # Tracking Deployment
    app_in_deployment = models.BooleanField(default=False)
    auto_redeploy = models.BooleanField(default=False)

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        if not self.id:
            self.slug = slugify(self.project_name)
        super().save(force_insert, force_update, *args, **kwargs)

    class Meta:
        abstract = True

    def get_app_type(self):
        return self.app_type

    def get_app_dir(self) -> str:
        return self.get_app_process().get_project_directory()

    def get_log_file(self) -> str:
        """
        Get deploy log path for current project

        :return: path
        :rtype: str
        """

        return self.get_app_process().get_log_file()

    # For status icon html classes
    def get_status_icon(self) -> Type[str | None]:
        """
        Get icon value for status

        :return: icon name
        :rtype: Type[str | None]
        """

        status_icon = {
            'inactive': 'grav',
            'pending': 'spinner',
            'deployed': 'check',
            'failed': 'bug',
            'disabled': 'times'
        }
        return status_icon.get(self.status)

    def raw_link(self) -> str:
        """
        Get the app full link

        :return: link
        :rtype: str
        """

        return f"{self.subdomain.get_name()}.{self.domain.domain}"

    def get_link(self) -> str:
        """
        Append http to app raw link

        :return: link
        :rtype: str
        """

        return f"http://{self.raw_link()}"

    @property
    def process(self) -> ServerProcess:
        return self.server.get_process()

    __app_process: AppProcess = None

    def create_app_process(self) -> AppProcess:
        return AppProcess(
            name=self.slug,
            branch=self.branch,
            clone_url=self.get_process_clone_url(),
            url=self.get_link(),
            host=self.server.ip_address,
            username=self.server.username,
            password=self.server.password,
            web_server=self.server.web_server
        )

    def get_app_process(self) -> AppProcess:
        if self.__app_process is None:
            self.__app_process = self.create_app_process()
        return self.__app_process

    def get_web_server_conf(self) -> str:
        """
        Get web server configuration for project

        :return: web server configuration path
        :rtype: str
        """
        return self.process.web_server.get_file_available_path(self.slug)

    def update_app_status(self, status: str):
        self.status = status

    def failed_deploy(self):
        self.update_app_status('failed')

    def success_deploy(self):
        self.update_app_status('deployed')

    def pending_deploy(self):
        self.update_app_status('pending')

    def get_process_clone_url(self) -> str:
        clone_url: str = self.repository.clone_url
        github_username = self.repository.github_user.get_account_name()
        github_password = cryptor.decrypt(
            self.repository.github_user.account.password)

        clone_url = clone_url.replace(
            'https://', f"https://{github_username}:{github_password}@")
        return clone_url

    def __str__(self) -> str:
        return self.project_name


class ReactApp(BaseApp):
    app_type = 'react'

    def create_app_process(self) -> ReactProcess:
        return ReactProcess(
            name=self.slug,
            branch=self.branch,
            clone_url=self.get_process_clone_url(),
            url=self.get_link(),
            host=self.server.ip_address,
            username=self.server.username,
            password=self.server.password,
            web_server=self.server.web_server
        )

    def deploy_process(self):
        """
        Start deploy process for app
        """

        process: ReactProcess = self.get_app_process()
        app_logger = process.get_logger()
        app_logger.info('Started deploying process')
        self.app_in_deployment = True
        self.pending_deploy()
        self.save()

        try:
            process.create_client()
            process.create_project_directory()
            process.git_clone()
            process.git_checkout()
            process.git_pull()
            process.npm_install()
            process.add_homepage()
            process.npm_build()
            access_log, error_log = process.configure_server()
            self.access_log = access_log
            self.error_log = error_log
            process.enable_web_server()
            process.restart_web_server()
            self.success_deploy()
            app_logger.info('Project is successfully deployed.')

        except Exception as e:
            app_logger.info(
                'Error while trying to deploy app directory on server')
            app_logger.exception(e)
            self.failed_deploy()

        process.destroy()
        app_logger.info('Finished Deploying\n\n')
        self.app_in_deployment = False
        self.save()
