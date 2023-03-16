import json
import threading
import time  # noqa
from typing import Dict, List, Type, Union  # noqa

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from services.models import Service, Website, WebsiteUrl
from utils.general import get_required_data, is_ajax, refactor_errors
from utils.github import GithubClient
from utils.logger import err_logger, logger  # noqa
from utils.mixins import GetServer, DnsUtilityMixin
from utils.typing import DnsType

from .forms import (GetLogForm, GithubAccountUserUpdateForm, GithubCreateForm,
                    GithubUpdateForm, SubdomainForm, DeleteSubdomainForm)
from .models import (Domain, GithubAccount, Repository, RepositoryUser, Server,
                     Subdomain)


@csrf_exempt
def github_receive_webhook(request):
    """
    Github webhook view
    """

    request_meta: dict = request.META
    request_body: bytes = request.body

    try:
        HTTP_X_GITHUB_HOOK_ID = request_meta.get('HTTP_X_GITHUB_HOOK_ID')
        repository = Repository.objects.filter(
            hook_id=HTTP_X_GITHUB_HOOK_ID).first()

        if repository:
            SIGNATURE = request_meta.get('HTTP_X_HUB_SIGNATURE_256')

            if GithubClient.validate_payload(
                request_body,
                repository.get_webhook_secret(),
                SIGNATURE
            ):
                hook_data: dict = json.loads(request_body.decode())

                # Get the branch
                branch = None
                ref: str = hook_data.get('ref')
                refs = ref.split('/')
                if refs[1] == 'heads':
                    branch = refs[2]

                if branch is not None:
                    # Apps to run autodeploy
                    apps = repository.reactapp_set.filter(auto_redeploy=True)

                    for app in apps:
                        app_branch = app.branch if app.branch else 'master'

                        if app_branch == branch:
                            if app.app_in_process is False:
                                t = threading.Thread(target=app.deploy_process)
                                t.start()

                                message = f"""
                                Started automatically {app.project_name} """
                                logger.debug(message)

                return HttpResponse(status=200)

    except Exception as e:
        err_logger.exception(e)

    return HttpResponse(status=400)


class Dashboard(
    LoginRequiredMixin,
    GetServer, generic.TemplateView
):
    """
    Main dashboard view
    """

    template_name = 'panel/index.html'
    select_server_redirect = False
    extra_context = {
        'title': 'Dashboard',
    }
    # permission_required = ('panel.view_server',)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get available servers
        context["servers"] = Server.objects.all()

        # Get websites
        context['websites'] = Website.objects.all()

        # Get github accounts
        context['github_accounts'] = GithubAccount.objects.all()
        return context


class FileManagerView(
    LoginRequiredMixin,
    GetServer, generic.TemplateView
):
    template_name = 'panel/file-manager.html'
    extra_context = {
        'title': 'File manager',
    }


class ServerPage(LoginRequiredMixin, generic.DetailView):
    """
    Server dashboard page
    """

    template_name = 'panel/server_page.html'
    slug_field = 'slug_name'
    slug_url_kwarg = 'slug_name'
    model = Server
    context_object_name = 'server'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        object = self.get_object()

        # Set server_name session
        self.request.session['server_name'] = object.slug_name

        # Set title
        context['title'] = object.name

        # Get available services
        context["services"] = Service.objects.all()

        # Get websites
        context['websites'] = Website.objects.filter(server=object)
        return context


def recheck_server_websites(request, slug_name: str):
    """
    Recheck websites on server

    :param slug_name: Server instance slug name
    :type slug_name: str
    :return: redirect to server dashboard page
    """

    server = get_object_or_404(Server, slug_name=slug_name)
    server.recheck()

    messages.success(request, 'Websites are all rechecked')
    return redirect(reverse(
        'panel:server_page', kwargs={'slug_name': slug_name}))


def update_server_websites(request, slug_name):
    """
    Create, delete or updates enabled websites

    :return: redirect to server dashboard page
    """

    server = get_object_or_404(Server, slug_name=slug_name)
    websites = server.get_enabled_sites()

    for data in websites:
        clean_data = server.parse_website_data(data)

        current_urls = clean_data.pop('urls')

        website, _ = Website.objects.update_or_create(
            server=server,
            conf_filename=clean_data['conf_filename'],
            defaults=clean_data)

        website_urls = website.websiteurl_set.all()

        for site in website_urls:
            if site.url not in current_urls:
                site.delete()
            else:
                current_urls.remove(site.url)

        for url in current_urls:
            WebsiteUrl.objects.create(url=url, website=website)

    messages.success(request, 'Website list successfully updated')
    return redirect(
        reverse('panel:server_page', kwargs={'slug_name': slug_name}))


class ServiceLog(LoginRequiredMixin, GetServer, generic.DetailView):
    template_name = 'panel/log_tab.html'
    model = Service
    slug_field = 'service_name'
    slug_url_kwarg = 'service_name'
    context_object_name = 'service'

    def get_context_data(self, **kwargs):
        """
        Update the context for this view

        :return: context
        :rtype: dict
        """

        context = super().get_context_data(**kwargs)
        service = self.get_object()
        context["title"] = service.name
        return context


class WebsiteLog(LoginRequiredMixin, GetServer, generic.DetailView):
    template_name = 'panel/website_tab.html'
    model = Website
    slug_field = 'conf_filename'
    slug_url_kwarg = 'conf_filename'
    context_object_name = 'website'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        website = self.get_object()

        # Get service name
        context["title"] = website.name

        return context


def recheck_service_status(request, service_name):
    obj = get_object_or_404(Service, service_name=service_name)

    # Update status
    obj.recheck()

    messages.success(
        request, f"{obj.name} service status is successfully reloaded")

    return redirect(obj.get_absolute_url())


def get_logs_view(request):

    if request.POST:
        service_name = request.POST.get('service_name')

        obj = get_object_or_404(Service, service_name=service_name)

        # Get the service logs
        data = {
            'log': obj.get_logs()
        }

        return JsonResponse(data=data, status=200)

    messages.warning(request, 'Page does not exist')
    return redirect('panel:dashboard')


def recheck_website_status(request, conf_filename):
    obj = get_object_or_404(Website, conf_filename=conf_filename)

    # Update status
    obj.recheck()
    messages.success(
        request, f"{obj.name} links status is successfully reloaded")
    return redirect(obj.get_absolute_url())


def get_websites_logs_view(request, conf_filename):

    obj = get_object_or_404(Website, conf_filename=conf_filename)

    if request.POST:
        data = request.POST.copy()
        data['access'] = obj.access_log
        data['error'] = obj.error_log
        form = GetLogForm(data)

        if form.is_valid():
            # Get log_type
            log_type = form.cleaned_data.get('log_type')
            data = {
                'log': obj.get_logs(log_type)
            }
            return JsonResponse(data=data, status=200)

        errors = form.errors
        data = {
            'errors': errors
        }
        return JsonResponse(data=data, status=400)

    messages.warning(request, 'Log does not exist')
    return redirect(reverse(
        'panel:server_page', kwargs={'slug_name': obj.server.slug_name}))


class DomainList(LoginRequiredMixin, GetServer, generic.ListView):
    select_server_redirect = False
    template_name = 'panel/domains.html'
    model = Domain
    ordering = ['domain']
    extra_context = {
        'title': 'Domain Lists'
    }
    context_object_name = 'list_domains_processed'


def update_domain_list(request):
    """
    Function based view to update the domain list from available
    domain name service providers

    :param request: _description_
    :type request: _type_
    :return: _description_
    :rtype: _type_
    """
    # Get domains from dns providers
    dns_clients: Dict[str, Type[DnsType]] = Domain.get_dns_clients()

    for _id, client in dns_clients.items():
        domains: List[Dict[str, str]] = client.get_domains_list()
        for domain in domains:
            # Get the bootstrap tag to use for the status
            status = domain.get('status')
            status_tag = 'success' if status == 'active' else 'danger'

            new_obj = {
                'domain': domain.get('domain'),
                'domain_id': domain.get('id'),
                'status': status,
                'status_tag': status_tag,
                'soa_email': domain.get('soa_email'),
                'domain_provider': _id
            }

            Domain.objects.update_or_create(
                domain_id=new_obj['domain_id'],
                defaults=new_obj
            )

    messages.success(request, 'Domain list is successfully updated')

    return redirect('panel:domain-list')


class DomainDetail(
    LoginRequiredMixin, GetServer, DnsUtilityMixin, generic.DetailView
):
    select_server_redirect = False
    template_name = 'panel/domain-detail.html'
    model = Domain
    slug_field = 'domain_id'
    slug_url_kwarg = 'domain_id'
    context_object_name = 'domain'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get the domain and set title
        domain = self.object
        context['title'] = domain.domain

        main_domain_ip = ''
        list_records_processed = []

        # Get subdomains for domain
        subdomains = Subdomain.objects.filter(domain_id=domain.domain_id)

        for domain_obj in subdomains:
            name = domain_obj.name
            target = domain_obj.target
            record_id = domain_obj.record_id

            # Find the main domain name and id
            if name == '':
                main_domain_ip = target
                continue

            new_obj = {
                'name': name,
                'target': target,
                'record_id': record_id,
            }

            list_records_processed.append(new_obj)

        context['list_records_processed'] = list_records_processed
        context['main_domain_ip'] = main_domain_ip

        return context

    def get_create_subdomain_data(self):
        req_data = ['name', 'target', 'ttl_sec']
        return get_required_data(self.request.POST, req_data)

    def create_subdomain(
        self, client: DnsType,
        domain_id: str, data: dict = None
    ):
        context = dict()

        if data is None:
            data = self.get_create_subdomain_data()

        errors = []
        http_status = 400

        form = SubdomainForm(data=data)
        if form.is_valid():
            data = form.cleaned_data
            result = self.create_subdomain_record(client, domain_id, data)

            message = "New subdomain created \
successfully, reloading page now."
            errors = result.get('errors')
        else:
            errors = refactor_errors(form.errors)

        if errors:
            context['errors'] = errors
            message = 'Error occured while trying \
to create domain, check errors.'
        else:
            http_status = 200

        context['message'] = message

        return JsonResponse(data=context, status=http_status)

    def delete_subdomain(
        self, client: DnsType,
        domain_id: str, record_id: str
    ):
        context = dict()
        data = {
            'record_id': record_id
        }

        errors = []
        http_status = 400

        form = DeleteSubdomainForm(data=data)
        if form.is_valid():
            status, result = client.delete_subdomain(domain_id, record_id)
            errors = result.get('errors')
            if status is True:
                message = "Poof! Your subdomain record has been deleted!"
                http_status = 200
                form.delete()
            errors = result.get('errors')
        else:
            errors = refactor_errors(form.errors)

        if errors:
            context['errors'] = errors
            message = 'Error deleting subdomain record'

        context['message'] = message
        return JsonResponse(data=context, status=http_status)

    def update_subdomain(self, client: DnsType, domain_id: str):
        context = dict()
        req_data = ['name', 'target', 'record_id']
        data = get_required_data(self.request.POST, req_data)
        record_id = data.get('record_id')

        errors = []
        http_status = 400

        form = SubdomainForm(data=data)
        if form.is_valid():
            status, result = client.update_record(data, domain_id, record_id)
            errors = result.get('errors')
            if status is True:
                message = "Yay! Your subdomain record has been updated!"
                http_status = 200
                form.update()
            errors = result.get('errors')
        else:
            errors = refactor_errors(form.errors)

        if errors:
            context['errors'] = errors
            message = 'Error updating subdomain record'
        context['message'] = message

        return JsonResponse(data=context, status=http_status)

    def post(self, request, *args, **kwargs):
        if is_ajax(request):
            domain: Type[Domain] = self.get_object()
            client: Type[DnsType] = domain.get_dns_client()

            type_name = request.POST.get('type')
            if type_name == 'delete':
                record_id = request.POST.get('record_id')
                return self.delete_subdomain(
                    client, domain.domain_id, record_id)
            elif type_name == 'update':
                return self.update_subdomain(client, domain.domain_id)
            else:
                return self.create_subdomain(client, domain.domain_id)


def update_subdomain_list(request, domain_id: str):
    """
    Function based view to update the domain list
    from main domain dns provider

    :param domain_id: Domain id in database
    :type domain_id: string
    :return: Http redirect to domain detail page
    """
    # Get the domain and set title
    domain: Type[Domain] = get_object_or_404(Domain, domain_id=domain_id)
    client: Type[DnsType] = domain.get_dns_client()

    # Get subdomains for domain
    subdomains = Subdomain.objects.filter(domain_id=domain.domain_id)

    # Set updated subdomain list
    updated_sub_list = []

    dns_subdomains = client.get_subdomains(domain.domain_id)

    for record in dns_subdomains:
        name = record.get('name')
        target = record.get('target')
        record_id = record.get('id')

        # Check if the record id is already in the db
        try:
            # Get subdomain
            subdomain = subdomains.get(record_id=record_id)

            # Update it
            subdomain.name = name
            subdomain.target = target
            subdomain.save()

            # Append to updated subdomain list
            updated_sub_list.append(subdomain)

        except Subdomain.DoesNotExist:
            # Create new subomain
            new_obj = {
                'name': name,
                'target': target,
                'record_id': record_id,
                'domain_id': domain_id,
            }
            new_obj = Subdomain.objects.create(**new_obj)
            updated_sub_list.append(new_obj)

    # Delete subdomains that are not processed. Because this means that
    # they are not in dns provider domain list anymore
    for current in subdomains:
        # value to know whether it is there or not
        is_available = False
        for new in updated_sub_list:
            if new.id == current.id:
                is_available = True
                break
        # Delete current meaning that it is not in the updated list at all
        if not is_available:
            current.delete()

    messages.success(request, 'Domain list is successfully updated')

    return redirect(reverse('panel:domain-detail', args=[domain_id]))


class GithubAccountList(LoginRequiredMixin, GetServer, generic.ListView):
    select_server_redirect = False
    template_name = 'panel/github_accounts.html'
    model = GithubAccount
    context_object_name = 'github_accounts'
    extra_context = {
        'title': 'Github Accounts'
    }


class GithubAccountDetail(LoginRequiredMixin, GetServer, generic.DetailView):
    select_server_redirect = False
    template_name = 'panel/github_account.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    model = GithubAccount
    context_object_name = 'github_account'
    extra_context = {
        'title': 'Github Account Page'
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        object = self.get_object()

        # Get available repositories
        context["repository_users"] = object.repositoryuser_set.all()

        return context


class GithubAccountCreate(LoginRequiredMixin, GetServer, generic.TemplateView):
    select_server_redirect = False
    template_name = 'panel/add_github.html'
    extra_context = {
        'title': 'Create New Github Account'
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Init form
        context['form'] = GithubCreateForm(
            initial={
                'password': '',
                'username': '',
                'white_list_organizations': '',
                'black_list_organizations': '',
            })

        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()

        form = GithubCreateForm(data=request.POST)

        if form.is_valid():
            account = form.save()
            messages.success(request, 'Github account successfully created')
            return redirect(reverse(
                'panel:github_detail', kwargs={"username": account.username}))

        context['form'] = form

        return render(request, self.template_name, context)


class GithubAccountUpdate(LoginRequiredMixin, GetServer, generic.DetailView):
    select_server_redirect = False
    template_name = 'panel/edit_github.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    model = GithubAccount
    context_object_name = 'github_account'
    extra_context = {
        'title': 'Update Github Account'
    }

    def get_context_data(self, **kwargs):
        object = self.get_object()
        self.object = object

        context = super().get_context_data(**kwargs)

        # Get available repositories
        context["repository_users"] = object.repositoryuser_set.all()

        # Init form
        context['form'] = GithubUpdateForm(
            instance=object, initial={'needed_password': ''})

        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()

        form = GithubUpdateForm(data=request.POST, instance=self.object)

        if form.is_valid():
            form.save()
            messages.success(request, 'Github account successfully updated')
            return redirect(reverse(
                'panel:github_update',
                kwargs={"username": self.object.username}))

        context['form'] = form

        return render(request, self.template_name, context)


class GithubAccountUserUpdate(
    LoginRequiredMixin, GetServer, generic.TemplateView
):
    select_server_redirect = False
    template_name = 'panel/update_github_account_user.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get keywords
        username = self.kwargs.get('username')
        account_name = self.kwargs.get('account_name')

        # Get Account
        github_account = get_object_or_404(GithubAccount, username=username)

        try:
            github_account_user = \
                github_account.repositoryuser_set.get(user=account_name)
        except RepositoryUser.DoesNotExist:
            raise Http404('Github User account does not exist')

        # Set title
        context['title'] = f"Update {username} - Account: {account_name}"

        # Init form
        context['form'] = GithubAccountUserUpdateForm(
            instance=github_account_user, initial={'needed_password': ''})

        # Add user to context
        context['github_account_user'] = github_account_user

        # Add username and account name to context for template
        context['username'] = username
        context['account_name'] = account_name

        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()

        github_account_user = context['github_account_user']
        form = GithubAccountUserUpdateForm(
            data=request.POST, instance=github_account_user)

        if form.is_valid():
            form.save()

            messages.success(
                request, 'Github account user successfully updated')
            return redirect(reverse(
                'panel:github_update_user',
                kwargs={
                    "username": context['username'],
                    'account_name': context['account_name']}))
        context['form'] = form

        return render(request, self.template_name, context)


def update_github_accounts(request, username):
    github_account = get_object_or_404(GithubAccount, username=username)

    # Update account users
    github_account.update_account_users()

    messages.success(
        request,
        f"{github_account.username} accounts are successfully updated")

    return redirect(reverse(
        'panel:github_detail', kwargs={"username": github_account.username}))


def delete_github_account(request, username):
    github_account = get_object_or_404(GithubAccount, username=username)

    # Update account users
    github_account.delete()

    messages.success(
        request, f"{github_account.username} Account is successfully deleted")

    return redirect('panel:dashboard')


def update_repos(request, username, account_name):
    # Get Account
    github_account = get_object_or_404(GithubAccount, username=username)

    try:
        github_account_user =\
            github_account.repositoryuser_set.get(user=account_name)
    except RepositoryUser.DoesNotExist:
        raise Http404('Github User account does not exist')

    # Update status
    github_account_user.update_repos()

    messages.success(
        request,
        f"""Github account user repositories
        for {account_name} are successfully reloaded""")

    return redirect(reverse(
        'panel:github_detail', kwargs={"username": username}))
