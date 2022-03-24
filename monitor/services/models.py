from django.db import models
from django.utils import timezone
from django.urls import reverse

from utils.general import get_version, get_active_state, get_service_logs, get_website_state, get_website_logs

class Service(models.Model):
    name = models.CharField(max_length=40)
    service_name = models.CharField(max_length=40, unique=True)
    active = models.BooleanField(default=True)
    last_checked = models.DateTimeField(null=True, blank=True, editable=False)

    def __str__(self) -> str:
        return self.name

    def recheck(self):
        status = get_active_state(self.service_name)
        if status:
            self.active = True
        else:
            self.active = False
        self.last_checked = timezone.now()
        self.save()
    
    def get_logs(self):
        return get_service_logs(self.service_name)
    
    def get_version(self):
        return get_version(self.service_name)
    
    def get_last_status(self) -> str:
        return 'active' if self.active else 'inactive'
    
    def get_absolute_url(self):
        return reverse('panel:service', args=[self.service_name])


class Website(models.Model):
    name = models.CharField(max_length=40)

    # These data are without their extension
    conf_filename = models.CharField(max_length=100, unique=True)
    log_filename = models.CharField(max_length=100)

    website_link = models.URLField(unique=True)
    active = models.BooleanField(default=True)
    last_checked = models.DateTimeField(null=True, blank=True, editable=False)

    def __str__(self) -> str:
        return self.name
    
    # Get the location of the website conf file
    def get_conf_full_path(self):
        return f"/etc/apache2/sites-enabled/{self.conf_filename}.conf"
    
    # Get the full path to the log of the website
    def get_log_full_path(self):
        return f"/var/log/apache2/{self.log_filename}"

    # Recheck the status of the website
    def recheck(self):
        status = get_website_state('http://'+self.website_link)
        if status:
            self.active = True
        else:
            self.active = False
        self.last_checked = timezone.now()
        self.save()
    
    # Get the logs of the website
    def get_logs(self):
        return get_website_logs(self.get_log_full_path())
    
    # Get the status of the website in text
    def get_last_status(self) -> str:
        return 'active' if self.active else 'inactive'
    
    def get_absolute_url(self):
        return reverse('panel:website', args=[self.conf_filename])