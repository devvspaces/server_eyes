from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.db import models
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from django.urls import reverse

from panel.models import Server

from utils.general import printt as print
from utils.general import cryptor


class SelectServerException(Exception):
    """Server is not selected"""

    def __init__(self):
        super().__init__('SelectServerException')

class CustomTestMixin(UserPassesTestMixin):

    def test_func(self):
        return self.request.user.is_in_staff

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            # Set the next session
            next = self.request.META.get('PATH_INFO')
            link = reverse('account:login')+f'?next={next}'
            print(link)
            return redirect(link)

        messages.warning(self.request, 'Page not found')
        return redirect('dashboard:home')



# Get server and add to context
class GetServer(object):
    select_server_redirect = True
    server = None

    # Get's the server slug name from session and get's server from db
    def get_server(self):
        # Get server name
        server_name = self.kwargs.get('server_name')
        if not server_name:

            # Try to get server name from session
            server_name = self.request.session.get('server_name')

            if not server_name:
                if self.select_server_redirect:
                    raise SelectServerException
        
        try:
            if server_name:
                # Get server obj
                server = Server.objects.get(slug_name=server_name)
                self.server = server

                return server
        
        except Server.DoesNotExist:
            raise SelectServerException

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get server name and Add server to context
        context["server"] = self.get_server()

        return context