import os
import time, threading

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import generic
from django.utils.html import escape

from panel.models import Domain, Subdomain, Repository
from utils.general import convert_error, is_ajax, linodeClient, start_redeploy_process
from utils.logger import *
from utils.mixins import GetServer

from .models import ReactApp
from .forms import ReactDeployForm



class ReactDeployedApps(LoginRequiredMixin, GetServer, generic.ListView):
    template_name = 'deployer/deploys.html'
    extra_context = {
        'title': 'React Apps'
    }
    model = ReactApp
    context_object_name = 'apps'

    def get_queryset(self):
        qset = super().get_queryset()
        return qset.filter(server=self.get_server())


class ReactDeployNewapp(LoginRequiredMixin, GetServer, generic.TemplateView):
    template_name = 'deployer/deploy-react-app.html'
    extra_context = {
        'title': 'Deploy New React App'
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add the repository here
        context["repos"] = Repository.objects.all()

        # Get the domains available
        context['domains'] = Domain.objects.all()

        return context
    

    def post(self, request, *args, **kwargs):

        # Get class context
        cls_context = self.get_context_data()
        server = cls_context.get('server')

        context = dict()

        if is_ajax(request):
            # Validated data
            form = ReactDeployForm(data=request.POST)
            errors = []

            if form.is_valid():
                validated_data = form.cleaned_data

                # Get to variables
                project_name, repository, branch, domain, subdomain, link = validated_data.values()

                # Set the target ip
                target_ip = server.ip_address

                # Check if new subdomain link is passed
                if link:
                    # Create new subdomain
                    data = {
                        'name': link,
                        'target': target_ip,
                    }

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
                        subdomain = Subdomain.objects.create(**new_obj)
                    
                    else:
                        errors = result['errors']
                
                else:
                    # Meaning Subdomain is seleted
                    # If subdomain target is not same as hosting server
                    url_values = {
                        '-domainId-': domain.domain_id,
                        '-recordId-': subdomain.record_id,
                    }

                    # Update data
                    data = {
                        'target': target_ip
                    }
                    status, result = linodeClient.fetch_post(method='put', endpoint='record_update', data=data, url_values=url_values)

                    if status == 200:
                        # Update our db subdomain target
                        subdomain.target = target_ip
                        subdomain.save()
                        
                    else:
                        errors = result['errors']

                if not errors:
                    # Save app
                    new_app = {
                        'project_name': project_name,
                        'repository': repository,
                        'branch': branch,
                        'domain': domain,
                        'subdomain': subdomain,
                        'server': server,
                    }

                    app = ReactApp.objects.create(**new_app)

                    messages.success(request, f'App is successfully created')

                    context['redirect'] = str(reverse('deploy:react-app', kwargs={'slug': app.slug}))

                    return JsonResponse(data=context, status=200)

            else:
                errors = {'errors': form.errors}

                # Convert error to linode format
                errors = convert_error(errors)
                if errors is not None:
                    errors = errors['errors']
                    
            context['errors'] = errors

            return JsonResponse(data=context, status=400)



class DeployDetail(LoginRequiredMixin, GetServer, generic.DetailView):
    template_name = 'deployer/detail.html'
    model = ReactApp
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    context_object_name = 'app'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        app = self.object

        context["title"] = f'App ({app.project_name})'

        return context


@login_required
def deploy_app(request, slug):
    app = ReactApp.objects.get(slug=slug)

    # Check if app not already in deployment
    if app.app_in_deployment == False:
        t = threading.Thread(target=start_redeploy_process, args=[app])
        t.start()
    else:
        messages.warning(request, 'Current app already in deployment, wait for task to complete.')

    return redirect(reverse('deploy:react-app', kwargs={'slug': app.slug}))



# Setup auto redeploy
@login_required
def setup_auto_redeploy_app(request, slug):
    app = ReactApp.objects.get(slug=slug)

    # Invert previous value if True then becomes False - vice versa
    app.auto_redeploy = not app.auto_redeploy
    app.repository.create_webhook(request)
    app.save()

    # Check whether to delete repository repo webhook or not
    # Delete only when there is no other deployed apps with auto redeploy = True
    count_app_with_auto_redeploy = app.repository.reactapp_set.filter(auto_redeploy=True).count()
    if count_app_with_auto_redeploy == 0:
        app.repository.delete_webhook()

    messages.success(request, 'Auto redeploy process updated')

    return redirect(reverse('deploy:react-app', kwargs={'slug': app.slug}))


# Fetch logs for app deploy process
class FetchDeployLog(LoginRequiredMixin, GetServer, generic.View):
    
    def get(self, request, *args, **kwargs):
        slug = kwargs.get('slug')
        app = ReactApp.objects.get(slug=slug)

        if is_ajax(request):
            if request.method == 'GET':
                log_dir = app.get_log_file()
                with open(log_dir, 'r') as file:
                    text = file.read()

                    if len(text) == 0:
                        text = 'No logs yet'

                    # Replace \n
                    # text = text.replace('\n', '<br/>')
                    text = escape(text)
                    # text = text.replace('\n', '<br/>')

                    context = dict()
                    context['data'] = text

                    return JsonResponse(data=context, status=200)
        
        return JsonResponse(dict(), status=400)
        
    def post(self, request, *args, **kwargs):
        slug = kwargs.get('slug')
        app = ReactApp.objects.get(slug=slug)

        if is_ajax(request):
            if request.method == 'POST':
                log_dir = app.get_log_file()
                with open(log_dir, 'w') as file:
                    file.write('')

                    return JsonResponse(dict(), status=200)
        
        return JsonResponse(dict(), status=400)
    


