from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from utils.general import verify_next_link
from .forms import LoginForm
from django.urls import reverse
from django.shortcuts import redirect, render


def login_view(request):
    """
    Login view to sign in users
    """
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

    return render(request, 'account/login.html', context)


def logout_view(request):
    """
    Logout view to sign out users

    :return: redirect to login view
    :rtype: HttpResponseRedirect
    """
    logout(request)
    return redirect('account:login')
