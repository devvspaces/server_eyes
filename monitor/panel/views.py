import time

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import FormView, DetailView, TemplateView

from utils.general import verify_next_link

from services.models import Service, Website

from .forms import LoginForm

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


class Dashboard(LoginRequiredMixin, TemplateView):
    template_name = 'panel/index.html'

    extra_context = {
        'title': 'Dashboard'
    }


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get available services
        context["services"] = Service.objects.all()
        return context


class Dashboard(LoginRequiredMixin, TemplateView):
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


class ServiceLog(LoginRequiredMixin, DetailView):
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


class WebsiteLog(LoginRequiredMixin, DetailView):
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