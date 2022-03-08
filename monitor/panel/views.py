from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import FormView, UpdateView, TemplateView

from utils.general import verify_next_link

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