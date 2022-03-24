from django.contrib import admin

# Register your models here.
from .models import Service, Website

admin.site.register([Service, Website])