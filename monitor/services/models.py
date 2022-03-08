from django.db import models

class Service(models.Model):
    name = models.CharField(max_length=40)
    active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name