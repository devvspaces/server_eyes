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
    server = models.ForeignKey('panel.Server', on_delete=models.CASCADE, null=True)

    name = models.CharField(max_length=200)
    conf_filename = models.CharField(max_length=200, unique=True)

    # This will be the file full paths
    access_log = models.TextField(blank=True)
    error_log = models.TextField(blank=True)

    # Other logs (first useful for apache configurations) (this will be used to store json string)
    other_logs = models.TextField(blank=True)

    active = models.BooleanField(default=False)
    last_checked = models.DateTimeField(null=True, blank=True, editable=False)

    def __str__(self) -> str:
        return self.name
    
    # Get the location of the website conf file
    def get_conf_full_path(self):
        return f"/etc/apache2/sites-enabled/{self.conf_filename}"
    
    def get_access_log(self):
        return self.access_log
    
    def get_error_log(self):
        return self.error_log

    # Recheck the status of the website
    def recheck(self):
        # Get all website url under website
        urls = self.websiteurl_set.all()
        for url in urls:
            url.recheck()
    
    # Get the logs of the website
    def get_logs(self, log_type:str):
        return get_website_logs(self, log_type)
    
    # Get the status of the website in text
    def get_last_status(self) -> str:
        return 'active' if self.active else 'inactive'
    
    def get_absolute_url(self):
        return reverse('panel:website', args=[self.conf_filename])


class WebsiteUrl(models.Model):
    website = models.ForeignKey(Website, on_delete=models.CASCADE)
    url = models.CharField(max_length=200)

    active = models.BooleanField(default=True)
    last_checked = models.DateTimeField(null=True, blank=True, editable=False)


    # Recheck the status of the website
    def recheck(self):
        status = get_website_state('http://' + self.url)
        if status:
            self.active = True

            # Update parent to active too
            self.website.active = True
            
        else:
            self.active = False
        
        self.website.last_checked = timezone.now()
        self.website.save()
        self.last_checked = timezone.now()
        self.save()
    

    # Get the status of the website in text
    def get_last_status(self) -> str:
        return 'active' if self.active else 'inactive'
        

    def __str__(self) -> str:
        return self.url