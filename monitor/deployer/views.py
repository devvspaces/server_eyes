from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import generic

from panel.models import Domain
from utils.general import convert_error, is_ajax

from .models import Repository
from .forms import ReactDeployForm



class ReactDeployedApps(LoginRequiredMixin, generic.TemplateView):
    template_name = 'deployer/deploys.html'
    extra_context = {
        'title': 'React Apps'
    }

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
                print('Form is valid\n\n')
            else:
                errors = {'errors': form.errors}

                # Convert error to linode format
                errors = convert_error(errors)
                if errors is not None:
                    errors = errors['errors']
            
            context['errors'] = errors

            print(context)
        
            return JsonResponse(data=context, status=400)