from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.utils.safestring import mark_safe

from utils.validators import validate_special_char
from utils.model_mixins import ModelChangeFunc


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
    project_name = models.CharField(max_length=255, validators=[validate_special_char], unique=True)
    slug = models.SlugField(max_length=512, unique=True, blank=True)
    project_dir = models.CharField(max_length=255)
    conf_dir = models.CharField(max_length=255)

    # Repository
    repository = models.ForeignKey('panel.Repository', on_delete=models.CASCADE)
    branch = models.CharField(max_length=50, help_text='Branch on repository to deploy, this checkouts to default master branch if not specified')

    # Domain
    domain = models.ForeignKey('panel.Domain', on_delete=models.DO_NOTHING, null=True)
    subdomain = models.ForeignKey('panel.Subdomain', on_delete=models.DO_NOTHING, null=True)

    # Status
    status = models.CharField(choices=STATUS, default='inactive', max_length=255)

    # Tracking Deployment
    app_in_deployment = models.BooleanField(default=False)
    auto_redeploy = models.BooleanField(default=False)


    # Monitor field setup
    # Used to update github autoredo
    # def update_slug(obj):
    #     obj.slug = slugify(obj.project_name)

    # monitor_change = {
    #     'project_name': update_slug
    # }


    def update_slug(self):
        self.slug = slugify(self.project_name)

    def save(self, force_insert=False, force_update=False, *args, **kwargs):

        if not self.id:
            self.update_slug()

        super().save(force_insert, force_update, *args, **kwargs)


    class Meta:
        abstract = True

    
    def get_app_type(self):
        return self.app_type

    # Get the directory to place all clone repositories (projects code base directory)
    def get_deploy_project_directory(self) -> str:
        return f'/home/{self.server.username}/ServerMonitor/deploys/projects'
    

    # Get the directory to clone repository (project code base directory)
    def get_app_dir(self) -> str:
        return f"{self.get_deploy_project_directory()}/{self.slug}"
    

    # Get deploy log directory for current project
    def get_log_file(self) -> str:
        return f"{settings.BASE_DIR}/logs/deployed_apps/{self.slug}/deploy.log"
    
    
    # For status icon html classes
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

    # This is used to get the project full link
    def raw_link(self):
        return f"{self.subdomain.get_name()}.{self.domain.domain}"

    # This is used to append https to project full link for html link tags or more
    def get_link(self):
        return f"http://{self.raw_link()}"
    

    # Get web server configuration for project
    def get_web_server_conf(self):

        webserver_conf_dict = {
            'apache': self.get_apache_conf,
            'nginx': self.get_nginx_conf,
        }
        
        func = webserver_conf_dict.get(self.server.web_server)
        
        if func is not None:
            return func()
    
    # Get server configuration for apache server
    def get_apache_conf(self):
        return f"/etc/apache2/sites-available/{self.slug}.conf"
    
    # Get server configuration for nginx server
    def get_nginx_conf(self):
        return f"/etc/nginx/sites-available/{self.slug}.conf"


    def __str__(self) -> str:
        return self.project_name


class ReactApp(BaseApp):
    app_type = 'react'

    
    
