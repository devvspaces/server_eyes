from django.contrib import admin
from utils.admin_mixins import ExtraAdminFeature

from .forms import GithubCreateForm, ServerCreateForm
from .models import (Domain, GithubAccount, Repository, RepositoryUser, Server,
                     Subdomain)

admin.site.register([Domain, Subdomain, Repository, RepositoryUser])


class ServerAdmin(ExtraAdminFeature):
    add_form = ServerCreateForm

    list_display = ('name', 'username',)
    list_filter = ('web_server',)
    search_fields = ('name', 'username',)

    fieldsets = (
        ('Server', {
            'fields': (
                'ip_address', 'name', 'server_os_name',
                'server_os_version', 'server_os_url',)}),
        ('Advanced', {'fields': ('slug_name', 'username', 'web_server')}),
    )

    add_fieldsets = (
        ('Server', {'fields': ('ip_address', 'name',)}),
        ('Advanced', {'fields': ('username', 'web_server', 'password',)}),
    )

    ordering = ('name',)


class GithubAccountAdmin(ExtraAdminFeature):
    add_form = GithubCreateForm

    list_display = ('username', 'active', 'created', 'updated',)
    list_filter = ('active',)
    search_fields = ('username', 'updated',)

    fieldsets = (
        ('Github Account', {'fields': ('username', 'active',)}),
    )

    add_fieldsets = (
        ('Github Account', {'fields': ('username', 'password',)}),
    )

    ordering = ('created', 'updated',)


admin.site.register(Server, ServerAdmin)
admin.site.register(GithubAccount, GithubAccountAdmin)



import datetime
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE

class MonitorLog(admin.ModelAdmin):
    list_display = ('action_time','user','content_type','object_repr','change_message','action_flag')
    list_filter = ['action_time','user','content_type']
    ordering = ('-action_time',)

admin.site.register(LogEntry, MonitorLog)
