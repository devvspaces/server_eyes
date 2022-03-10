from django.db import models
from django.utils import timezone
from django.urls import reverse

from utils.general import get_version, get_active_state, get_service_logs

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
        self.active = False
        self.last_checked = timezone.now()
    
    def get_logs(self):
        return get_service_logs(self.service_name)
    
    def get_version(self):
        return get_version(self.service_name)
    
    def get_last_status(self) -> str:
        return 'active' if self.active else 'inactive'
    
    def get_absolute_url(self):
        return reverse('panel:service', args=[self.service_name])