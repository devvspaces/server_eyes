from typing import Dict, Type, Union

from django import forms
from panel.models import Domain, Subdomain
from utils.validators import validate_special_char

from .models import ReactApp


#: Type for cleaned data returned in ReactDeployForm
CleanDataType = Dict[str, Union[str, Type[Domain], Type[Subdomain]]]


class ReactDeployForm(forms.ModelForm):
    cleaned_data: CleanDataType = {}
    domain = forms.IntegerField(required=True)
    subdomain = forms.IntegerField(required=False)
    link = forms.CharField(
        required=False,
        max_length=255, validators=[validate_special_char])

    class Meta:
        model = ReactApp
        fields = ('project_name', 'repository', 'branch',)

    def validate_git(self, data: dict):
        """
        Verify the github branch and repository

        :param data: Data from form fields
        :type data: dict
        :raises forms.ValidationError: Valid repository
        :raises forms.ValidationError: Valid branch
        """
        repository = data.get('repository')
        branch = data.get('branch')

        if not repository:
            raise forms.ValidationError(
                {'repository': 'You must select a repository'})

        if branch not in repository.get_branches():
            raise forms.ValidationError(
                {"branch": 'Select a valid branch. \
That branch is not one of the available branches.'})

    def validate_domains(self, data: dict):
        """
        Validate the domain selected, updates the value
        of domain key in data passed as input to Type[Domain]

        :param data: Data from form fields
        :type data: dict
        :raises forms.ValidationError: validation error
        """
        domain = data.get('domain')
        try:
            domain: Type[Domain] = Domain.objects.get(id=domain)
            self.validate_subdomain_name(data, domain.domain_id)
            data['domain'] = domain
        except Domain.DoesNotExist:
            raise forms.ValidationError(
                {"domain": 'Select a valid domain. \
That domain is not one of the available domains.'})

    def validate_subdomain_name(self, data: dict, domain_id: str):
        """
        Validate the sub domain selected, updates the value
        of subdomain key in data passed as input to Type[Subdomain]

        :param data: Data from form fields
        :type data: dict
        :param domain_id: selected domain domain_id
        :type domain_id: str
        :raises forms.ValidationError: validation error
        """
        subdomain = data.get('subdomain')
        if subdomain:
            # Validate the selected subdomain belongs to domain
            try:
                subdomain: Type[Subdomain] = Subdomain.objects.get(
                    record_id=subdomain)
                if subdomain.domain_id != domain_id:
                    raise Subdomain.DoesNotExist
                data['subdomain'] = subdomain
            except Subdomain.DoesNotExist:
                raise forms.ValidationError(
                    {"subdomain": 'Select a valid option. \
Selected option is not one of the available subdomains.'})
        else:
            self.validate_link_name(data)

    def validate_link_name(self, data: dict):
        """
        Validate new subdomain name

        :param data: Data from form fields
        :type data: dict
        :raises forms.ValidationError: validation error
        """
        link = data.get('link')
        if not link:
            raise forms.ValidationError(
                {"link": 'Must select a subdomain \
or provide a new one to be created.'})

    def clean(self) -> CleanDataType:
        """
        _summary_

        :return: _description_
        :rtype: CleanDataType
        """
        # self.cleaned_data: CleanDataType = self.cleaned_data
        cleaned_data = self.cleaned_data

        self.validate_domains(cleaned_data)
        self.validate_git(cleaned_data)

        return cleaned_data
