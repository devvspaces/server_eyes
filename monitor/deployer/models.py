from django.db import models

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
        ('pending', 'Pending',),
        ('deploying', 'Deploying in progress',),
        ('deployed', 'Deployed',),
        ('failed', 'Failed',),
    )

    project_name = models.CharField(max_length=255, validators=[validate_special_char])
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE)
    branch = models.CharField(max_length=255)
    domain = models.ForeignKey('panel.Domain', on_delete=models.DO_NOTHING, null=True)
    subdomain = models.ForeignKey('panel.Subdomain', on_delete=models.DO_NOTHING, null=True)
    project_dir = models.CharField(max_length=255)
    conf_dir = models.CharField(max_length=255)
    status = models.CharField(choices=STATUS, default='pending', max_length=255)

    def __str__(self) -> str:
        return self.project_name
