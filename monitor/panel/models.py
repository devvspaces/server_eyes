from django.db import models



class Domain(models.Model):
    domain = models.URLField()
    domain_id = models.IntegerField(unique=True)
    status = models.CharField(max_length=50)
    status_tag = models.CharField(max_length=50)
    soa_email = models.EmailField()

    def __str__(self):
        return self.domain


class Subdomain(models.Model):
    record_id = models.IntegerField(unique=True)
    domain_id = models.IntegerField()
    name = models.CharField(max_length=255)
    target = models.GenericIPAddressField()

    def __str__(self):
        return self.name