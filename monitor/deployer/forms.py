from django import forms

from panel.models import Domain, Subdomain
from utils.validators import validate_special_char

from .models import ReactApp

class ReactDeployForm(forms.ModelForm):
    domain = forms.IntegerField(required=True)
    subdomain = forms.IntegerField(required=False)
    link = forms.CharField(required=False, max_length=255, validators=[validate_special_char])

    class Meta:
        model = ReactApp
        fields = ('project_name', 'repository', 'branch',)
    
    def clean(self):
        cleaned_data = self.cleaned_data

        # Verify the main domain and subdomain or link
        domain = cleaned_data.get('domain')
        subdomain = cleaned_data.get('subdomain')
        link = cleaned_data.get('link')

        try:
            domain = Domain.objects.get(id=domain)

            # Check if subdomain was passed
            if subdomain:
                # Validate the selected subdomain belongs to domain
                try:
                    subdomain = Subdomain.objects.get(record_id=subdomain)
                    if subdomain.domain_id != domain.domain_id:
                        raise Subdomain.DoesNotExist
                except Subdomain.DoesNotExist:
                    raise forms.ValidationError({"subdomain": 'Select a valid subdomain. That subdomain is not one of the available subdomains.'})
            else:
                # There must be a link passed
                if not link:
                    raise forms.ValidationError({"link": 'Must select a subdomain or provide a new one to be created.'})


        except Domain.DoesNotExist:
            raise forms.ValidationError({"domain": 'Select a valid domain. That domain is not one of the available domains.'})
        
        # Verify the github branch
        repository = cleaned_data.get('repository')
        branch = cleaned_data.get('branch')

        if branch not in repository.get_branches():
            raise forms.ValidationError({"branch": 'Select a valid branch. That branch is not one of the available branches.'})
        

        # Update cleaned data
        cleaned_data['domain'] = domain
        cleaned_data['subdomain'] = subdomain
        

        return cleaned_data