from typing import Type
from django import forms
from utils.general import cryptor
from utils.github import GithubClient
from utils.validators import validate_special_char
from utils.logger import err_logger, logger  # noqa

from .models import GithubAccount, RepositoryUser, Server, Subdomain


class SubdomainForm(forms.Form):
    name = forms.CharField(validators=[validate_special_char])
    target = forms.GenericIPAddressField()
    ttl_sec = forms.IntegerField(required=False)
    record_id = forms.CharField(required=False)
    subdomain: Type[Subdomain] = None

    def clean_record_id(self):
        record_id = self.cleaned_data.get('record_id')
        if record_id:
            try:
                self.subdomain = Subdomain.objects.get(record_id=record_id)
            except Subdomain.DoesNotExist:
                raise forms.ValidationError('Subdomain does not exist')
        return record_id

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        record_id = cleaned_data.get('record_id')
        name = name.lower()

        subdomains_qset = Subdomain.objects.filter(name=name)
        if record_id:
            subdomains_qset = subdomains_qset.exclude(record_id=record_id)

        if subdomains_qset.exists():
            raise forms.ValidationError(
                {'name': 'Subdomain name already exist'})
        cleaned_data['name'] = name
        return cleaned_data

    def update(self) -> Type[Subdomain]:
        """
        Updating Subdomain objects

        :return: Subdomain
        :rtype: Type[Subdomain]
        """
        for attr, _ in self.fields.items():
            value = self.cleaned_data.get(attr)
            setattr(self.subdomain, attr, value)
        self.subdomain.save()
        return self.subdomain


class DeleteSubdomainForm(forms.Form):
    record_id = forms.CharField()

    def clean_record_id(self) -> Type[Subdomain]:
        record_id = self.cleaned_data.get('record_id')
        try:
            return Subdomain.objects.get(record_id=record_id)
        except Subdomain.DoesNotExist:
            raise forms.ValidationError('Subdomain does not exist')

    def delete(self):
        record_id: Type[Subdomain] = self.cleaned_data.get('record_id')
        record_id.delete()


# Server create form for admin
class ServerCreateForm(forms.ModelForm):
    class Meta:
        model = Server
        fields = ("ip_address", "web_server", "name", "username", "password")

    # Cleaning password to encrypt password
    def clean_password(self):
        password = self.cleaned_data.get("password")
        password = cryptor.encrypt(password)
        return password


class GetLogForm(forms.Form):
    LOG_TYPE = (
        ('access', "Access"),
        ('error', "Error"),
        ('other', "Other"),
    )
    log_type = forms.ChoiceField(choices=LOG_TYPE)
    from_date = forms.DateField(required=False)
    to_date = forms.DateField(required=False)
    access = forms.CharField(max_length=255, required=False)
    error = forms.CharField(max_length=255, required=False)

    def clean(self):
        cleaned_data = super().clean()
        access = cleaned_data['access']
        error = cleaned_data['error']
        log_type = cleaned_data['log_type']
        if log_type == 'access':
            if not access:
                raise forms.ValidationError(
                    {'log_type': 'Access log is not available'})
        elif log_type == 'error':
            if not error:
                raise forms.ValidationError(
                    {'log_type': 'Error log is not available'})

        return cleaned_data


class GithubCreateForm(forms.ModelForm):
    class Meta:
        model = GithubAccount
        fields = (
            "username", "password", 'white_list_organizations',
            'black_list_organizations',)

    def clean(self):
        cleaned_data = super().clean()

        # Validate if username and password are valid on github
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        # Decrypt password
        decrypted_password = cryptor.decrypt(password)

        # Init github client
        client = GithubClient(password=decrypted_password)

        if username and password and not client.validate_github_account():
            err = "Make sure to provide a valid Github Username and Password"
            raise forms.ValidationError({"username": err, "password": err})

        return cleaned_data

    # Cleaning password to encrypt password
    def clean_password(self):
        password = self.cleaned_data.get("password")
        password = cryptor.encrypt(password)
        return password

    def save(self, commit=True):
        github_account = super().save()
        github_account.update_account_users()
        return github_account


class GithubUpdateForm(forms.ModelForm):
    needed_password = forms.CharField(max_length=255)

    class Meta:
        model = GithubAccount
        fields = (
            "username", 'needed_password',
            'white_list_organizations', 'black_list_organizations',)

    # Cleaning password to encrypt password
    def clean_needed_password(self):
        needed_password = self.cleaned_data.get("needed_password")

        # Decrpty current password
        current_password = cryptor.decrypt(self.instance.password)

        # Validate needed_password
        if current_password != needed_password:
            raise forms.ValidationError('Current password is not correct')

        return needed_password


class GithubAccountUserUpdateForm(forms.ModelForm):
    needed_password = forms.CharField(max_length=255)

    class Meta:
        model = RepositoryUser
        fields = ("show_private_repo",)

    # Cleaning password to encrypt password
    def clean_needed_password(self):
        needed_password = self.cleaned_data.get("needed_password")

        # Decrpty current password
        current_password = cryptor.decrypt(self.instance.account.password)

        # Validate needed_password
        if current_password != needed_password:
            raise forms.ValidationError('Current password is not correct')

        return needed_password
