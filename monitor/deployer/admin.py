from django.contrib import admin

# Register your models here.
from .models import ReactApp, Repository

admin.site.register([ReactApp, Repository])