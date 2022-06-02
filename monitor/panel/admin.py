from django.contrib import admin

from .models import Domain, Subdomain, Server, GithubAccount, Repository, RepositoryUser
from .forms import ServerCreateForm, GithubCreateForm

from utils.admin_mixins import ExtraAdminFeature

admin.site.register([Domain, Subdomain, Repository, RepositoryUser])


class ServerAdmin(ExtraAdminFeature):
    add_form = ServerCreateForm

    list_display = ('name', 'username',)
    list_filter = ('web_server',)
    search_fields= ('name', 'username',)

    fieldsets = (
        ('Server', {'fields': ('ip_address', 'name',)}),
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
    search_fields= ('username', 'updated',)

    fieldsets = (
        ('Github Account', {'fields': ('username', 'active',)}),
    )

    add_fieldsets = (
        ('Github Account', {'fields': ('username', 'password',)}),
    )

    ordering = ('created', 'updated',)


admin.site.register(Server, ServerAdmin)
admin.site.register(GithubAccount, GithubAccountAdmin)