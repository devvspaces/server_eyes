import time, threading

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import generic

from panel.models import Domain, Subdomain
from utils.general import convert_error, is_ajax, linodeClient, redeploy_process
from utils.logger import *

from .models import Repository, ReactApp
from .forms import ReactDeployForm



class ReactDeployedApps(LoginRequiredMixin, generic.ListView):
    template_name = 'deployer/deploys.html'
    extra_context = {
        'title': 'React Apps'
    }
    model = ReactApp
    context_object_name = 'apps'

class ReactDeployNewapp(LoginRequiredMixin, generic.TemplateView):
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
        context = dict()
        if is_ajax(request):
            # Validated data
            form = ReactDeployForm(data=request.POST)
            errors = []

            if form.is_valid():
                validated_data = form.cleaned_data


                # Get to vars
                project_name, repository, branch, domain, subdomain, link = validated_data.values()


                # Check if new subdomain link is passed
                if link:
                    # Get the target ip
                    target_ip = ''

                    # Get subdomains for domain
                    subdomains = Subdomain.objects.filter(domain_id=domain.domain_id)

                    for domain_obj in subdomains:
                        target = domain_obj.target
                        if name == '':
                            target_ip = target
                            break

                        
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

                    errors = result['errors']

                if not errors:
                    # Save app
                    new_app = {
                        'project_name': project_name,
                        'repository': repository,
                        'branch': branch,
                        'domain': domain,
                        'subdomain': subdomain,
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

            print(context)
        
            return JsonResponse(data=context, status=400)



class DeployDetail(LoginRequiredMixin, generic.DetailView):
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
    
    t = threading.Thread(target=redeploy_process, args=[app])
    t.start()

    return redirect(reverse('deploy:react-app', kwargs={'slug': app.slug}))

class FetchDeployLog(LoginRequiredMixin, generic.View):
    
    def get(self, request, *args, **kwargs):
        slug = kwargs.get('slug')
        app = ReactApp.objects.get(slug=slug)

        if is_ajax(request):
            if request.method == 'GET':
                with open(app.get_log_dir(), 'r') as file:
                    text = file.read()

                    if len(text) == 0:
                        text = 'No logs yet'

                    # Replace \n
                    text = text.replace('\n', '<br/>')

                    context = dict()
                    context['data'] = text

                    return JsonResponse(data=context, status=200)
        
        return JsonResponse(dict(), status=400)
        
    def post(self, request, *args, **kwargs):
        slug = kwargs.get('slug')
        app = ReactApp.objects.get(slug=slug)

        if is_ajax(request):
            if request.method == 'POST':
                with open(app.get_log_dir(), 'w') as file:
                    file.write('')

                    return JsonResponse(dict(), status=200)
        
        return JsonResponse(dict(), status=400)
    


