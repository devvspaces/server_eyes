from typing import Dict, Type, Union
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

from panel.models import Server, Subdomain

from utils.general import printt as print
from utils.typing import DnsType


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


class GetServer(object):
    """
    Get server and add to context

    :param object: _description_
    :type object: _type_
    :raises SelectServerException: _description_
    :raises SelectServerException: _description_
    :return: _description_
    :rtype: _type_
    """
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


class DnsUtilityMixin:
    """
    Simple utility mixin with functions
    for subdomain views
    """
    def create_subdomain_record(
        self, client: DnsType, domain_id: str, data: dict
    ) -> Dict[str, Union[str, Type[Subdomain]]]:
        """
        _summary_

        :param client: _description_
        :type client: DnsType
        :param domain_id: _description_
        :type domain_id: str
        :param data: _description_
        :type data: dict
        :return: _description_
        :rtype: Dict[str, Union[str, int, Type[Subdomain]]]
        """
        data['type'] = 'A'

        status, result = client.create_subdomain(
            data, domain_id)
        subdomain = None

        if status is True:
            target = result['target']
            name = result['name']
            record_id = result['id']

            new_obj = {
                'target': target,
                'name': name,
                'record_id': record_id,
                'domain_id': domain_id,
            }

            subdomain = Subdomain.objects.create(**new_obj)

        result = {
            'subdomain': subdomain,
            'errors': result.get('errors')
        }
        return result
