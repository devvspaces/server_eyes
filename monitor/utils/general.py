import json

import logging

# Create the logger and set the logging level
logger = logging.getLogger('basic')
err_logger = logging.getLogger('basic.error')

from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.shortcuts import redirect

# from agency.models import AgencyMembership


from cryptography.fernet import Fernet, InvalidToken

from django.conf import settings

class Crypthex:
    def __init__(self):
        self.key = settings.ENCRYPTING_KEY

        # Instance the Fernet class with the key
        self.fernet = Fernet(self.key.encode())

    def encrypt(self, text):
        text = str(text)
        # Use the fernet created in the __init__ to encrypt text, which will return an encoded string
        # example of result = b'example'
        result = self.fernet.encrypt(text.encode())
        return result.decode()

    def decrypt(self, text):
        text = str(text)
        try:
            # Use the fernet created in the __init__ to decrypt text, which will return an encoded string
            # example of result = b'example'
            result = self.fernet.decrypt(text.encode())
            return result.decode()
        except InvalidToken:
            pass

        return False

cryptor = Crypthex()


def invalid_str(value):
    # This checks if a string contains special chars or not
    for i in '@#$%^&*+=://;?><}{[]()':
        if i in value:
            return True
    return False


def choices_to_dict(dicts=None):
    if dicts == None:
        dicts = {}
    
    return [{'value':a[0], 'name':a[1]} for a in dicts]


# Print that only works when on
def printt(*args, **kwargs):
    if settings.PRINT_LOG:
        return print(*args, **kwargs)


# def send_email(email, subject, message, fail=True):
#     if settings.DEBUG:
#         print(message)
    
#     if settings.OFF_EMAIL:
#         return True
        
#     val = send_mail(subject=subject, message=message, from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[email], fail_silently=fail)
#     return True if val else False


def send_email(email, subject, message, fail=True):
    if settings.DEBUG == True:
        print(message)
    
    # if settings.OFF_EMAIL:
    #     return True

    val = send_mail(subject=subject, message=message, html_message=message, from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[email], fail_silently=fail)

    print(f'The value of sent email is {val}')
    return True if val else False


# Code to remover session if it exists
def remove_session(request, name):
    session = request.session.get(name, None)
    if session is not None:
        del request.session[name]


# Code to convert tuple that looks like a dict to a list of python dictionary
def tup_to_dict(tup:tuple) -> dict:
    jsonObj = []

    for key,value in tup:
        obj = dict()
        obj['key'] = key
        obj['value'] = value
        jsonObj.append(obj)

    return json.dumps(jsonObj)

import socket

def verify_ip(ip):
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        pass
    return False

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    if verify_ip(ip):
        return ip


def verify_next_link(next):
    if next:
        if next.startswith('/'):
            return next

def get_next_link(request):
    next = request.GET.get('next')
    return verify_next_link(next)


def check_agent_agency(request):
    try:
        request.user.agencymembership
        messages.warning(request, 'You already belong to an agency')
        return redirect('agency:agent_list_dash')
    # except AgencyMembership.DoesNotExist:
    except Exception as e:
        pass


def filter_cleaned(val:str, expected='str'):
    returnee = '*********asdfasdfqw352346*******'

    if val:
        val = val.strip()
        if val.isdigit():
            return int(val)
        return val
    
    if expected == 'int':
        returnee = 0

    return returnee


def decamelize(text):
    if text:
        texts = text.split('_')
        texts = [i.capitalize() for i in texts]
        return ' '.join(texts)
    
    return ''


def check_user_membership(request):
    # Check if user has any active membership
    if request.user.get_membership() is None:
        messages.warning(request, 'You have no active plan')
        return redirect('dash:board')

def add_queryset(a, b):
    return a | b
