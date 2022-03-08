from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.models import User
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.hashers import check_password
from django.shortcuts import get_object_or_404




class LoginForm(forms.Form):
    username   = forms.CharField()
    password   = forms.CharField(widget=forms.PasswordInput())

    def clean(self):
        data=super(LoginForm, self).clean()
        username = data.get('username')
        password = data.get('password')

        try:
            user = User.objects.get(username=username)
            if not user.check_password(password):
                raise forms.ValidationError({'username':'Please enter the correct username and password.'})
        except User.DoesNotExist as e:
            raise forms.ValidationError({'username':'Please enter the correct username and password.'})
        return data