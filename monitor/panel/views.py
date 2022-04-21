import time
import re

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import generic

from utils.general import verify_next_link, linodeClient, get_required_data

from services.models import Service, Website

from .forms import LoginForm
from .models import Domain

# Create your views here.
def login_view(request):
    context = {}
    form = LoginForm()

    if request.POST:
        form = LoginForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)

                # Get next link
                next = verify_next_link(request.POST.get('next'))
                next = next if next else reverse('panel:dashboard')

                messages.success(request, f"Welcome, {username}.")
                return redirect(next)
    
    context['form'] = form

    return render(request, 'panel/login.html', context)

def logout_view(request):
    logout(request)
    return redirect('panel:login')


class Dashboard(LoginRequiredMixin, generic.TemplateView):
    template_name = 'panel/index.html'

    extra_context = {
        'title': 'Dashboard'
    }


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get available services
        context["services"] = Service.objects.all()
        return context


class Dashboard(LoginRequiredMixin, generic.TemplateView):
    template_name = 'panel/index.html'

    extra_context = {
        'title': 'Dashboard'
    }


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get available services
        context["services"] = Service.objects.all()

        # Get websites
        context['websites'] = Website.objects.all()
        return context


class ServiceLog(LoginRequiredMixin, generic.DetailView):
    template_name = 'panel/log_tab.html'
    model = Service
    slug_field = 'service_name'
    slug_url_kwarg = 'service_name'
    context_object_name = 'service'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        service = self.get_object()

        # Get service name
        context["title"] = service.name

        return context


class WebsiteLog(LoginRequiredMixin, generic.DetailView):
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

    messages.success(request, f"{obj.name} service status is successfully reloaded")

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

    messages.success(request, f"{obj.name} website status is successfully reloaded")

    return redirect(obj.get_absolute_url())

def get_websites_logs_view(request):

    if request.POST:
        conf_filename = request.POST.get('conf_filename')

        obj = get_object_or_404(Website, conf_filename=conf_filename)

        # Get the service logs
        data = {
            'log': obj.get_logs()
        }
    
        return JsonResponse(data=data, status=200)
    
    messages.warning(request, 'Page does not exist')
    return redirect('panel:dashboard')



class DomainList(LoginRequiredMixin, generic.TemplateView):
    template_name = 'panel/domains.html'

    extra_context = {
        'title': 'Domain Lists'
    }


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get domains from linode
        status, data = linodeClient.fetch_get('domains_list')
        list_domains_processed = []

        # Get if status is valid
        if status == 200:
            list_domains = data['data']

            # New obj
            for domain_obj in list_domains:

                # Get the bootstrap tag to use for the status
                status = domain_obj.get('status')
                status_tag = 'success' if status == 'active' else 'danger'

                new_obj = {
                    'domain': domain_obj.get('domain'),
                    'domain_id': domain_obj.get('id'),
                    'status': status,
                    'status_tag': status_tag,
                    'soa_email': domain_obj.get('soa_email'),
                }

                # Create or update domain objects
                Domain.objects.update_or_create(**new_obj)

                list_domains_processed.append(new_obj)
            
        context['list_domains_processed'] = list_domains_processed


        return context


class DomainDetail(LoginRequiredMixin, generic.DetailView):
    template_name = 'panel/domain-detail.html'
    model = Domain
    slug_field = 'domain_id'
    slug_url_kwarg = 'domain_id'
    context_object_name = 'domain'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get the domain and set title
        domain = self.object

        # Get domains records for domain from linode
        status, data = linodeClient.fetch_get('domain_records', url_values={'-domainId-': domain.domain_id})
        list_records_processed = []

        main_domain_ip = ''

        # Get if status is valid
        if status == 200:
            list_records = data['data']

            for domain_obj in list_records:
                record_type = domain_obj.get('type')
                name = domain_obj.get('name')
                target = domain_obj.get('target')

                if record_type == 'A':
                    # Find the main domain name and id
                    if name == '':
                        main_domain_ip = target
                        continue

                    new_obj = {
                        'name': name,
                        'target': target,
                    }

                    list_records_processed.append(new_obj)
            
        context['list_records_processed'] = list_records_processed
        context['main_domain_ip'] = main_domain_ip

        return context


    def post(self, request, *args, **kwargs):
        requested_html = re.search(r'^text/html', request.META.get('HTTP_ACCEPT'))
        if not requested_html:
            context= dict()

            # Get the domain object
            domain = self.get_object()

            # Get the data from the form
            req_data = ['name', 'target', 'ttl_sec']
            data = get_required_data(request.POST, req_data)

            # Add the record type to the data
            data['type'] = 'A'

            status, result = linodeClient.fetch_post(endpoint='domain_records', data=data, url_values={'-domainId-': domain.domain_id})

            if status == 200:
                # Get the target and name
                target, name = result['target'], result['name']

                data = {
                    'target': target,
                    'name': name,
                }

                context['data'] = data

                return JsonResponse(data=context, status=200)

            context['errors'] = result['errors']

            return JsonResponse(data=context, status=400)

