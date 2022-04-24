import time
import re

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import generic

from utils.general import verify_next_link, linodeClient, get_required_data, convert_error

from services.models import Service, Website

from .forms import LoginForm, SubdomainForm
from .models import Domain, Subdomain

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



class DomainList(LoginRequiredMixin, generic.ListView):
    template_name = 'panel/domains.html'
    model = Domain
    ordering = ['domain']
    extra_context = {
        'title': 'Domain Lists'
    }
    context_object_name = 'list_domains_processed'


# Function based view to update the domain list from linode
def update_domain_list(request):
    # Get domains from linode
    status, data = linodeClient.fetch_get('domains_list')

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
        
        messages.success(request, 'Domain list is successfully updated')

    return redirect('panel:domain-list')

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


    def post(self, request, *args, **kwargs):
        requested_html = re.search(r'^text/html', request.META.get('HTTP_ACCEPT'))
        if not requested_html:
            context= dict()

            # Get the domain object
            domain = self.get_object()

            # Get the data from the form
            req_data = ['name', 'target', 'ttl_sec']
            data = get_required_data(request.POST, req_data)

            errors = []

            # Validate the required data
            form = SubdomainForm(data=data)
            if form.is_valid():

                # Get the validated data
                data = form.cleaned_data

                # Add the record type to the data
                data['type'] = 'A'

                status, result = linodeClient.fetch_post(endpoint='domain_records', data=data, url_values={'-domainId-': domain.domain_id})

                if status == 200:
                    # Get the target and name
                    target, name, record_id = result['target'], result['name'], result['id']

                    new_obj = {
                        'target': target,
                        'name': name,
                        'record_id': record_id,
                        'domain_id': domain.domain_id,
                    }

                    context['data'] = new_obj

                    # Create new subdomain
                    Subdomain.objects.create(**new_obj)

                    return JsonResponse(data=context, status=200)
            
                errors = result['errors']
            
            else:
                errors = {'errors': form.errors}

                # Convert error to linode format
                errors = convert_error(errors)
                if errors is not None:
                    errors = errors['errors']

            context['errors'] = errors

            print(context)

            return JsonResponse(data=context, status=400)


# Function based view to update the domain list from linode
def update_subdomain_list(request, domain_id):
    # Get the domain and set title
    domain = get_object_or_404(Domain, domain_id=domain_id)

    # Get subdomains for domain
    subdomains = Subdomain.objects.filter(domain_id=domain.domain_id)
    print(subdomains, 'Firstly')

    # Set updated subdomain list
    updated_sub_list = []

    # Get domains records for domain from linode
    status, data = linodeClient.fetch_get('domain_records', url_values={'-domainId-': domain.domain_id})

    # Get if status is valid
    if status == 200:
        list_records = data['data']

        for domain_obj in list_records:
            record_type = domain_obj.get('type')
            name = domain_obj.get('name')
            target = domain_obj.get('target')
            record_id = domain_obj.get('id')

            # Check if the record is an A dns record
            if record_type == 'A':

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
                    print('Created')
                    new_obj = Subdomain.objects.create(**new_obj)
                    updated_sub_list.append(new_obj)
        
        # Delete subdomains that are not processed. Because this means that
        # they are not in linode anymore
        print(subdomains, updated_sub_list)
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



