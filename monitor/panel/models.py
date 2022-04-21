from django.db import models



class Domain(models.Model):
    domain = models.URLField()
    domain_id = models.IntegerField(unique=True)
    status = models.CharField(max_length=50)
    status_tag = models.CharField(max_length=50)
    soa_email = models.EmailField()