import datetime
import re
import shlex
import socket
import subprocess

import requests
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.utils.safestring import mark_safe

from .logger import err_logger, logger  # noqa


def update_obj(obj, fields: dict):
    """
    Function used to update model objects
    """
    for key, value in fields.items():
        setattr(obj, key, value)
    obj.save()


class Crypthex:
    def __init__(self):
        self.key = settings.ENCRYPTING_KEY

        # Instance the Fernet class with the key
        self.fernet = Fernet(self.key.encode())

    def encrypt(self, text):
        """
        Use the fernet created in the __init__ to encrypt
        text, which will return an encoded string
        example of result = b'example'
        """
        text = str(text)

        result = self.fernet.encrypt(text.encode())
        return result.decode()

    def decrypt(self, text):
        """
        Use the fernet created in the __init__ to decrypt text,
        which will return an encoded string
            example of result = b'example'
        """
        text = str(text)
        try:

            result = self.fernet.decrypt(text.encode())
            return result.decode()
        except InvalidToken:
            pass

        return False


cryptor = Crypthex()


def get_domain_name(request):
    """
    Get current hosting website domain name
    """
    site = get_current_site(request)
    return site.domain


def invalid_str(value):
    """
    This checks if a string contains special chars or not
    """
    for i in '@#$%^&*+=://;?><}{[]()':
        if i in value:
            return True
    return False


def choices_to_dict(tuples=None):
    """
    Convert choices in model to dictionary
    with 1st item in tuple as the key and the
    second as the value
    """

    if tuples is None:
        tuples = tuple()

    return [{'value': tuple[0], 'name': tuple[1]} for tuple in tuples]


def printt(*args, **kwargs):
    """
    Print that only works when on
    """

    if settings.PRINT_LOG:
        return print(*args, **kwargs)


def get_required_data(dict_like_obj, req_data=None):
    """
    This is a function used to get the required
    keys from a post or get request, to be passed
    to the api endpoint as a form or get data
    """

    if req_data is None:
        req_data = []

    data = {}

    for i in req_data:
        data[i] = dict_like_obj.get(i, '')

    return data


def send_email(email, subject, message, fail=True):
    """
    Send emails
    """

    if settings.DEBUG is True:
        print(message)

    if settings.OFF_EMAIL:
        return True

    value = send_mail(
        subject=subject, message=message,
        html_message=message, from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email], fail_silently=fail)

    return value == 1


def remove_session(request, name):
    session = request.session.get(name, None)
    if session is not None:
        del request.session[name]


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


def add_queryset(a, b):
    return a | b


def get_website_state(website):
    """
    Get the request status of a website,
    this is make a request to the url provided to see
    if it is working

    :param website: a url to check
    :type website: url
    :return: True or False depending on website response on request
    :rtype: bool
    """

    try:
        # Get the status of the website
        resp = requests.get(website)

        # True is response status is 200 or redirected
        return True if resp.status_code in [200, 302, 301] else False

    except Exception as e:
        err_logger.exception(e)

    return False


def get_in_dict_format(text: str):
    """
    Takes a string like this
        key=value
        key2=value2

    :param text: String in key=value format

    :return: a dictionary with key value pair
    :rtype: dict
    """

    text_list = text.splitlines()
    result_dict = dict()
    for key_value in text_list:
        key_value = key_value.strip()
        if key_value:
            key, value = key_value.split('=')
            result_dict[key] = value

    return result_dict


def get_name_from_text(name: str, text: str):
    """
    Get the value of a name from a text
    """

    search = f"{name}=(\w*)"  # noqa
    pattern = re.compile(search)
    match = pattern.search(text)
    if match:
        return match.group(1)


def convert_error(data: dict):
    """
    Function to convert errors from django format to linode format
    """

    # Set list of errors
    processed_errors = []

    errors: dict = data.get('errors')
    if (errors is None) or (isinstance(errors, dict) is False):
        raise ValueError('Data not in right format')

    # Loop through data to create this
    for key, value in errors.items():
        # Value would be a list of strings
        # Convert all of value to one string
        value = "\n".join(value)
        value = mark_safe(value)

        new_error = {
            'reason': value,
            'field': key,
        }
        processed_errors.append(new_error)

    # Return the processed errors
    return {'errors': processed_errors}


# Get if a request is an ajax request
def is_ajax(request):
    requested_html = re.search(r'^text/html', request.META.get('HTTP_ACCEPT'))
    return not requested_html


# Code to quickly run os commands in one line
def run_command(command, **kwargs):
    commands = shlex.split(command)
    return subprocess.run(commands, capture_output=True, text=True, **kwargs)


# Code to get total seconds from 1970 till now
def get_total_seconds_from_start():
    now = datetime.datetime.now()
    td = (now-datetime.datetime(1970, 1, 1))
    return td.total_seconds()
