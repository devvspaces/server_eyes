"""
Models for services and websites
"""


from typing import Type
from django.db import models
from django.urls import reverse
from django.utils import timezone
from utils.general import get_website_state
from utils.process import ServerProcess


class Service(models.Model):
    """
    Service model for services on server

    :param server: Server that service belongs to
    :type server: panel.models.Server
    :param name: Nice name for service
    :type name: str
    :param service_name: Service name in server
    :type service_name: str
    :param active: Service active status
    :type active: bool
    :param last_checked: Last time service active state was checked
    :type last_checked: datetime
    """

    server = models.ForeignKey(
        'panel.Server', on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=40)
    service_name = models.CharField(max_length=40, unique=True)
    active = models.BooleanField(default=True)
    last_checked = models.DateTimeField(null=True, blank=True, editable=False)

    def __str__(self) -> str:
        return self.name

    def connected_server_process(self) -> Type[ServerProcess]:
        """
        Get a connected server process from the main server

        :return: Server process object
        :rtype: Type[ServerProcess]
        """
        return self.server.get_connected_process()

    def recheck(self):
        """
        Check the status of this service
        """
        server_process = self.connected_server_process()
        self.active = server_process.get_active_state(self.service_name)
        self.last_checked = timezone.now()
        self.save()

    def get_logs(self):
        """
        Get the logs for this service
        """
        server_process = self.connected_server_process()
        return server_process.get_service_logs(self.service_name)

    def get_version(self):
        """
        Get service version

        :return: service version str
        :rtype: str
        """
        server_process = self.connected_server_process()
        return server_process.get_server_version(self.service_name)

    def get_last_status(self) -> str:
        """
        Get the status of the service as
        active or inactive

        :return: active or inactive
        :rtype: str
        """
        return 'active' if self.active else 'inactive'

    def get_absolute_url(self):
        """
        Get absolute url for service detail page

        :return: url for service detail page
        :rtype: django.urls.reverse
        """
        return reverse('panel:service', args=[self.service_name])


class Website(models.Model):
    """
    Website model to store website configurations gotten from
    servers

    :param server: Server instance gotten from
    :type server: panel.Server
    :param conf_filename: Configuration file name for website
    :type conf_filename: str
    :param conf_filepath: Full configuration file path for website
    :type conf_filepath: str
    :param access_log: Access log path in website configuration
    :type access_log: str
    :param error_log: Error log path in website configuration
    :type error_log: str
    :param other_logs: Other log paths apart from access and error log path
    found in website configuration
    :type other_logs: str
    :param active: Status of website availability.
    True if any of the urls under website is active
    :type active: bool
    :param last_checked: last time website was checked for activeness
    :type last_checked: datetime
    """

    server = models.ForeignKey(
        'panel.Server', on_delete=models.CASCADE, null=True)

    name = models.CharField(max_length=200)
    conf_filename = models.CharField(max_length=200)
    conf_filepath = models.CharField(max_length=255)

    # This will be the file full paths
    access_log = models.TextField(blank=True)
    error_log = models.TextField(blank=True)

    # Other logs (first useful for apache configurations)
    # (this will be used to store json string)
    other_logs = models.TextField(blank=True)

    active = models.BooleanField(default=False)
    last_checked = models.DateTimeField(null=True, blank=True, editable=False)

    def __str__(self) -> str:
        return self.name

    # Get the location of the website conf file
    # def get_conf_full_path(self):
    #     return f"/etc/apache2/sites-enabled/{self.conf_filename}"

    def get_access_log(self) -> str:
        """
        Get the website access log

        :return: website access log
        :rtype: str
        """
        return self.access_log

    def get_error_log(self) -> str:
        """
        Get the website error log

        :return: website error log
        :rtype: str
        """
        return self.error_log

    def recheck(self):
        """
        Recheck the status of the website and urls
        associated with it
        """
        urls = self.websiteurl_set.all()
        self.active = False
        for url in urls:
            if url.recheck() is True:
                self.active = True
        self.last_checked = timezone.now()
        self.save()

    def get_logs(self, log_type: str) -> str:
        """
        Get the logs of the website

        :param log_type: Type of log to get, acces or error
        :type log_type: str

        :return: Log text
        :rtype: str
        """
        if log_type == 'access':
            log_path = self.get_access_log()
        else:
            log_path = self.get_error_log()

        if log_path:
            server_process: Type[ServerProcess]\
                = self.server.get_connected_process()
            content = server_process.get_log_content(log_path)
            server_process.destroy()
            return content

    def get_last_status(self) -> str:
        """
        Get the status of the website in text

        :return: active or inactive
        :rtype: str
        """
        return 'active' if self.active else 'inactive'

    def get_absolute_url(self):
        """
        Get absolute url for website detail page

        :return: url for website detail page
        :rtype: django.urls.reverse
        """
        return reverse(
            'panel:website', args=[self.server.slug_name, self.conf_filename])


class WebsiteUrl(models.Model):
    """
    Website url model

    :param website: Website that this url belongs to
    :type website: Website model instance
    :param url: Website url
    :type url: str
    :param active: Website url active status
    :type active: bool
    :param last_checked: Last time website was checked
    :type last_checked: datetime
    """

    website = models.ForeignKey(Website, on_delete=models.CASCADE)
    url = models.CharField(max_length=200)
    active = models.BooleanField(default=True)
    last_checked = models.DateTimeField(null=True, blank=True, editable=False)

    def recheck(self) -> bool:
        """
        Recheck the status of the website and updates
        it active status

        :return: True or False for the url active status
        :rtype: bool
        """
        self.active = get_website_state('http://' + self.url)
        self.last_checked = timezone.now()
        self.save()
        return self.active

    def get_last_status(self) -> str:
        """
        Get the status of the website in text

        :return: active or inactive
        :rtype: str
        """
        return 'active' if self.active else 'inactive'

    def __str__(self) -> str:
        return self.url
