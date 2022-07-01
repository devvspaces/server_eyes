from django import forms
from django.contrib.auth.models import User


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
