from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import ListView

from agency.models import Property
from account.models import Profile

from utils.general import printt as print
from utils.general import choices_to_dict


class PropertyCreateMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_choices"] = choices_to_dict(Property.STATUS)
        context["property_type"] = choices_to_dict(Property.PROPERTY_TYPE)
        context["building_age"] = choices_to_dict(Property.BUILDING_AGE)
        return context
    
    def form_invalid(self, form):
        print(form.errors)
        return super().form_invalid(form)

class CustomTestMixin(UserPassesTestMixin):

    def test_func(self):
        return self.request.user.is_in_staff

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            # Set the next session
            next = self.request.META.get('PATH_INFO')
            link = reverse('account:login')+f'?next={next}'
            print(link)
            return redirect(link)

        messages.warning(self.request, 'Page not found')
        return redirect('dashboard:home')


class CustomerTestMixin(CustomTestMixin):

    def test_func(self):
        return self.request.user.is_customer

class NoStaffTestMixin(CustomTestMixin):

    def test_func(self):
        return not self.request.user.is_in_staff


class AllTestFunc:
    def __init__(self):
        self.object = None

    def test_func(self):
        # Get the order id
        print('This ran right here')
        order_id = self.kwargs.get('order_id')
        if self.request.user.is_in_staff:
            self.object = Order.objects.get(label__exact=order_id)
            return True
        elif self.request.user.is_customer:
            # Check if the order belongs to the customer
            qset = Order.objects.filter(label__exact=order_id, customer=self.request.user.customer)
            if qset.exists():
                self.object = qset.first()
                return True
        elif self.request.user.is_nerd:
            # Check if the order belongs to the nerd
            qset = Order.objects.filter(label__exact=order_id, nerd=self.request.user.nerd)
            if qset.exists():
                self.object = qset.first()
                return True


class CheckNerdOwnsOrder:
    def __init__(self):
        self.object = None

    def test_func(self):
        # Get the order id
        order_id = self.kwargs.get('order_id')
        if self.request.user.is_nerd:
            # Check if the order belongs to the nerd
            qset = Order.objects.filter(label__exact=order_id, nerd=self.request.user.nerd)
            if qset.exists():
                self.object = qset.first()
                return True


class WorkListMixin(ListView):
    model = Profile
    context_object_name = 'agents'
    paginate_by = 10
    account_type = 'estate_agent'

    def get_queryset(self):
        # time.sleep(4)
        submit = self.request.GET.get("submit")
        if submit:
            city = self.request.GET.get("city")
            state = self.request.GET.get("state")
            agent = self.request.GET.get("agent")

            return self.model.objects.filter(Q(city__icontains=city) & Q(state__icontains=state) & Q(fullname__icontains=agent) & Q(account_type=self.account_type))

        return self.model.objects.filter(account_type=self.account_type)



class CheckUserMembership:
    def get(self, request, *args, **kwargs):
        if self.request.user.get_membership():
            return super().get(request, *args, **kwargs)
        
        messages.warning(request, 'You have no active plan')
        return redirect('dash:board')


