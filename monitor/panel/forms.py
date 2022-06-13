from django import forms
from django.contrib.auth.models import User
from utils.general import cryptor
from utils.github import GithubClient
from utils.validators import validate_special_char

from .models import GithubAccount, RepositoryUser, Server


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput())

    def clean(self):
        data = super(LoginForm, self).clean()
        username = data.get('username')
        password = data.get('password')

        err_message = '''Please enter the correct
                        username and password.'''

        try:
            user = User.objects.get(username=username)
            if not user.check_password(password):
                raise forms.ValidationError(
                    {
                        'username': err_message
                    }
                )
        except User.DoesNotExist:
            raise forms.ValidationError({'username': err_message})

        return data


class SubdomainForm(forms.Form):
    name = forms.CharField(validators=[validate_special_char])
    target = forms.GenericIPAddressField()
    ttl_sec = forms.IntegerField(required=False)

    def clean_name(self):
        name = self.cleaned_data.get('name')
        return name.lower()


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
