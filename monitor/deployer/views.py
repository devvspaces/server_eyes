import threading
from typing import Type  # noqa

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import escape
from django.views import generic
from panel.models import Domain, Repository
from utils.general import get_domain_name, is_ajax, refactor_errors
from utils.logger import err_logger, logger  # noqa
from utils.mixins import DnsUtilityMixin, GetServer
from utils.typing import DnsType

from .forms import ReactDeployForm
from .models import ReactApp


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


class ReactDeployNewapp(
    LoginRequiredMixin, GetServer, DnsUtilityMixin, generic.TemplateView
):
    template_name = 'deployer/deploy-react-app.html'
    extra_context = {
        'title': 'Deploy New React App'
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["repos"] = Repository.objects.all()
        context['domains'] = Domain.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        """
        Create new react app deploys
        """
        cls_context: dict = self.get_context_data()
        server = cls_context.get('server')
        context = dict()

        if is_ajax(request):
            form = ReactDeployForm(data=request.POST)
            errors = []
            http_status = 400

            if form.is_valid():
                validated_data = form.cleaned_data
                project_name = validated_data.get('project_name')
                repository = validated_data.get('repository')
                branch = validated_data.get('branch')
                domain = validated_data.get('domain')
                subdomain = validated_data.get('subdomain')
                link = validated_data.get('link')
                client: Type[DnsType] = domain.get_dns_client()

                # Set the target ip
                target_ip = server.ip_address

                # Check if new subdomain link is passed
                if link:
                    data = {
                        'name': link,
                        'target': target_ip,
                    }

                    result = self.create_subdomain_record(
                        client, domain.domain_id, data)

                    subdomain = result.get('subdomain')
                    errors = result.get('errors')
                    http_status = result.get('http_status')
                else:
                    # Update subdomain target to the
                    # same as hosting server
                    data = {
                        'target': target_ip
                    }
                    status, result = client.update_record(
                        data, domain.domain_id, subdomain.record_id)

                    if status is True:
                        subdomain.target = target_ip
                        subdomain.save()

                    errors = result.get('errors')
            else:
                errors = refactor_errors(form.errors)

            if errors:
                context['errors'] = errors
                message = 'Error creating React app'
            else:
                new_app = {
                    'project_name': project_name,
                    'repository': repository,
                    'branch': branch,
                    'domain': domain,
                    'subdomain': subdomain,
                    'server': server,
                }

                app = ReactApp.objects.create(**new_app)
                context['redirect'] = str(
                    reverse('deploy:react-app', kwargs={'slug': app.slug}))
                message = 'React App is successfully created'
                messages.success(request, 'App is successfully created')

            context['message'] = message
            return JsonResponse(data=context, status=http_status)


class DeployDetail(
    LoginRequiredMixin, GetServer, generic.DetailView
):
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
    app: ReactApp = ReactApp.objects.get(slug=slug)

    # Check if app not already in deployment
    if app.app_in_process is False:
        t = threading.Thread(target=app.deploy_process)
        t.start()
    else:
        messages.warning(
            request, 'Already in process, wait for process to complete.')
    return redirect(reverse('deploy:react-app', kwargs={'slug': app.slug}))


@login_required
def pull_app_repository(request, slug):
    app: ReactApp = ReactApp.objects.get(slug=slug)

    # Check if app not already in deployment
    if app.app_in_process is False:
        t = threading.Thread(target=app.run_pull)
        t.start()
    else:
        messages.warning(
            request, 'Already in process, wait for process to complete.')
    return redirect(reverse('deploy:react-app', kwargs={'slug': app.slug}))


@login_required
def setup_auto_redeploy_app(request, slug):
    app = ReactApp.objects.get(slug=slug)

    # Invert previous value if True then becomes False - vice versa
    app.auto_redeploy = not app.auto_redeploy
    domain = get_domain_name(request)
    app.repository.create_webhook(domain)
    app.save()

    # Check whether to delete repository repo webhook or not
    # Delete only when there is no other deployed apps with
    # auto redeploy = True
    count_app_with_auto_redeploy\
        = app.repository.reactapp_set.filter(auto_redeploy=True).count()
    if count_app_with_auto_redeploy == 0:
        app.repository.delete_webhook()

    messages.success(request, 'Auto redeploy process updated')

    return redirect(reverse('deploy:react-app', kwargs={'slug': app.slug}))


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
