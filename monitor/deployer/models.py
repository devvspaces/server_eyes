from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.utils.safestring import mark_safe

from utils.validators import validate_special_char


# Github model
class Repository(models.Model):
    repo_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)
    clone_url = models.URLField()
    branches_url = models.URLField()
    branches = models.CharField(max_length=255)

    def get_branches(self):
        return self.branches.split(',')

    def __str__(self):
        return self.name


class ReactApp(models.Model):
    STATUS = (
        ('inactive', 'Inactive',),
        ('pending', 'Pending',),
        ('deployed', 'Deployed',),
        ('failed', 'Failed',),
        ('disabled', 'Disabled',),
    )

    project_name = models.CharField(max_length=255, validators=[validate_special_char], unique=True)
    slug = models.SlugField(max_length=512, unique=True)
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE)
    branch = models.CharField(max_length=255)
    domain = models.ForeignKey('panel.Domain', on_delete=models.DO_NOTHING, null=True)
    subdomain = models.ForeignKey('panel.Subdomain', on_delete=models.DO_NOTHING, null=True)
    project_dir = models.CharField(max_length=255)
    conf_dir = models.CharField(max_length=255)
    status = models.CharField(choices=STATUS, default='inactive', max_length=255)

    def get_dir(self):
        return f"{settings.DEPLOY_PROJECTS_DIR}{self.slug}"
    
    def get_log_dir(self):
        return f"{self.get_dir()}/deploy.log"
    
    def get_apache_conf(self):
        return f"/etc/apache2/sites-available/{self.slug}.conf"
    
    def get_status_icon(self):
        
        if self.status == 'inactive':
            return 'grav'
        elif self.status == 'pending':
            return 'spinner'
        elif self.status == 'deployed':
            return 'check'
        elif self.status == 'failed':
            return 'bug'
        elif self.status == 'disabled':
            return 'times'

    def raw_link(self):
        return f"{self.subdomain.get_name()}.{self.domain.domain}"

    def get_link(self):
        return f"http://{self.raw_link()}"

    def save(self, *args, **kwargs):
        if not self.id:
            self.slug = slugify(self.project_name)
        
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.project_name
