from django.db import models





class Domain(models.Model):
    domain = models.URLField()
    domain_id = models.IntegerField(unique=True)
    status = models.CharField(max_length=50)
    status_tag = models.CharField(max_length=50)
    soa_email = models.EmailField()

    def __str__(self):
        return self.domain
    
    def get_subdomain_js_string(self):
        # This function will be used to communicate with the deploy apps page
        # Get the subdomains
        subdomains = Subdomain.objects.filter(domain_id=self.domain_id)
        
        # Result list
        result = []

        for subdomain in subdomains:
            # Clean subdomain name
            sub_name = subdomain.name
            if sub_name:
                name = f"{sub_name}.{self.domain}"
            else:
                name = self.domain

            record_id = subdomain.record_id

            result.append(f"{name}*{record_id}")
        
        return '?'.join(result)


class Subdomain(models.Model):
    record_id = models.IntegerField(unique=True)
    domain_id = models.IntegerField()
    name = models.CharField(max_length=255)
    target = models.GenericIPAddressField()

    def get_name(self):
        if self.name == '.':
            return ''
        return self.name

    def __str__(self):
        return self.name
