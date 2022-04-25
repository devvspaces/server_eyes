import json, subprocess, os, re, shlex, requests
from cryptography.fernet import Fernet, InvalidToken

from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django.conf import settings


from .logger import *


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


import requests

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist



# Base api client
class BaseAPIClient:
    def __init__(self) -> None:
        # Set request methods
        # POST, PUT, PATCH, DELETE FUNCTIONS
        self.request = {
            'post': requests.post,
            'put': requests.put,
            'patch': requests.patch,
            'delete': requests.delete,
        }

    def get_headers(self):
        headers = self.headers
        return headers

    def build_uri(self, endpoint, url_values=None):
        # Get the rel url of the endpoint
        rel_url = self.endpoints.get(endpoint, '')

        if rel_url:

            # Get the url values
            if url_values is not None:
                for key, val in url_values.items():
                    rel_url = rel_url.replace(key, str(val))

            return f'{self.domain}{rel_url}'

        raise ObjectDoesNotExist('API endpoint does not exist')


    def fetch_post(self, method='post', endpoint='', data=None, url_values=None, files=None):
        # Get the endpoint
        url = self.build_uri(endpoint, url_values)

        print('Called post request', endpoint)

        if data is None:
            data = {}
        
        if files is None:
            files = {}

        if method == 'delete':
            response = self.request.get(method)(url, headers = self.get_headers())

            return response.status_code, dict()
        else:
            response = self.request.get(method)(url, json=data, headers = self.get_headers(), files=files)

            return response.status_code, response.json()


    def fetch_get(self, endpoint='', params=None, url_values=None):
        # Get the endpoint
        url = self.build_uri(endpoint, url_values)

        print('Called get request', endpoint)

        if params is None:
            params = {}

        response = requests.get(url, params=params, headers = self.get_headers())

        return response.status_code, response.json()



class LinodeClient(BaseAPIClient):
    def __init__(self):
        # Call BaseAPIClient init
        super().__init__()

        # Add the personal access token gotten from linode here
        self.personal_access_token = settings.LINODE_PAT
        self.headers = {
            'Authorization': f'Bearer {self.personal_access_token}',
        }

        # Set the linode api version here
        linode_api_version = settings.LINODE_API_VERSION
        self.domain = f"https://api.linode.com/{linode_api_version}/"

        # Define endpoints
        domains = 'domains'

        self.endpoints = {
            'domains_list': f'{domains}',
            'domain_records': f'{domains}/-domainId-/records',
            'record_update': f'{domains}/-domainId-/records/-recordId-',
        }

linodeClient = LinodeClient()


class GithubClient(BaseAPIClient):
    def __init__(self):
        # Call BaseAPIClient init
        super().__init__()

        # Add the personal access token gotten from github here
        # Set the github api version here
        git_api_version = settings.GITHUB_API_VERSION
        self.personal_access_token = settings.GITHUB_PAT
        self.headers = {
            'Authorization': f'Token {self.personal_access_token}',
            "Accept" : f"application/vnd.github.v{git_api_version}+json",
        }
        
        self.domain = f"https://api.github.com"

        # Define endpoints
        org = 'spacepen-dev'

        self.endpoints = {
            'repos': f'/orgs/{org}/repos',
            'branches': f'/repos/{org}/-repo-/branches',
        }
        
githubClient = GithubClient()



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



def get_required_data(dict_like_obj, req_data=None):
    """
    This is a function used to get the required keys from a post or get request,
    to be passed to the api endpoint as a form or get data
    """
    if req_data is None:
        req_data = []

    data = {}

    for i in req_data:
        data[i] = dict_like_obj.get(i, '')

    return data



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


# Code to get the version of a service in linux
def get_version(service_name):

    # Check if the server is 'posix'
    name = os.name
    if name == 'nt':
        return 'Windows'
    
    # Set the version arg
    version = 'v'
    args = {
        'V': ['mysql']
    }

    for key, val in args.items():
        if service_name in val:
            version = key

    process = subprocess.run([service_name, f'-{version}'], text=True, capture_output=True)
    if process.returncode == 0:
        output = process.stdout
        match = re.search(r"\d*\.\d*\.\d*", output)
        if match:
            return match.group()
    else:
        logger.debug(f'Error while trying to get version for {service_name}')
        logger.debug(process.stderr)
    
    return 'Empty'



def get_website_state(website):

    try:
        # Get the status of the website
        resp = requests.get(website)

        # True is response status is 200 or redirected
        return True if resp.status_code in [200, 302, 301] else False
    
    except Exception as e:
        err_logger.exception(e)


def get_active_state(service_name):

    # Check if the server is 'posix'
    name = os.name
    if name == 'nt':
        return 'Windows'

    process = subprocess.run(["systemctl", "show", service_name, '--no-page'], text=True, capture_output=True)
    if process.returncode == 0:
        output = process.stdout
        match = re.search('ActiveState=\w*', output)

        if match:
            result = match.group().strip('\n')

            # Get the status
            printt(result.split('='))
            status = result.split('=')[1]
            return True if status == 'active' else False
    else:
        logger.debug(f'Error while trying to get status for {service_name}')
        logger.debug(process.stderr)


def get_service_logs(service_name):

    # Check if the server is 'posix'
    name = os.name
    if name == 'nt':
        return mark_safe('test<br>test')

    command = f'journalctl -u {service_name} --no-page'
    # command = f'sudo -S journalctl -u {service_name} --no-page'
    # command = "sudo -S {command}"
    team_pass = settings.TEAM_KEY.encode()

    # Split commands with shlex
    commands = shlex.split(command)
    process = subprocess.run(commands, capture_output=True, text=True)
    # process = subprocess.Popen(commands, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # if True:
    try:

        print('Enter 1')

        print(process.returncode)
        # print(process.stderr.read())
        # print(process.stdout.read())

        print('Entered true')

        # Enter password
        # process.stdin.write(team_pass)

        # Get the logs
        logs = process.stdout

        print('GOt logs', logs)

        # Replace \n with <br> tags
        logs = logs.replace('\n', '<br><br>')

        print('Replaces newlines', logs)

        return mark_safe(logs)
    except Exception as e:
        print(f'Error while trying to get logs for {service_name}')
        logger.debug(f'Error while trying to get logs for {service_name}')
        err_logger.exception(e)
    
    # else:
    #     logger.debug(f'Error while trying to get logs for {service_name}')
    #     logger.debug(process.stderr)

    # os.popen("sudo -S %s"%(command), 'w').write('mypass')
    # os.popen("su root", 'w').write('mypass')

    return ''


def get_website_logs(log_path):

    # Check if the server is 'posix'
    name = os.name
    if name == 'nt':
        return mark_safe('test<br>test')

    command = f"sudo -S cat {log_path}"
    team_pass = settings.TEAM_KEY

    # Split commands with shlex
    commands = shlex.split(command)

    # Call commands and pass password
    process = subprocess.run(commands, capture_output=True, text=True, input=team_pass)

    try:

        logger.debug(f"Result for calling website log {process.returncode}")

        # Get the logs
        logs = process.stdout

        # Replace \n with <br> tags
        logs = logs.replace('\n', '<br><br>')

        return mark_safe(logs)
    except Exception as e:
        print(f'Error while trying to get logs for {log_path}')
        logger.debug(f'Error while trying to get logs for {log_path}')
        err_logger.exception(e)

    return ''


# Code to get enabled sites from apahce sites-enabled folder
def get_enabled_sites():

    # Check if the server is 'posix'
    name = os.name
    if name == 'nt':
        return [{'file_name': 'kogi.conf', 'log': 'kogi.log', 'url': 'kogi.spacepen.tech'}, {'file_name': 'kogi_test.conf', 'log': 'kogi_test.log', 'url': 'kogi_test.spacepen.tech'}, {'file_name': 'monitor.conf', 'log': 'monitor.log', 'url': 'epanel.spacepen.tech'}, {'file_name': 'ondo_farmers.conf', 'log': 'ondo_farmers.log', 'url': 'odk.spacepen.tech'}, {'file_name': 'site1.conf', 'log': 'spacepen.log', 'url': 'spacepen.tech'}]

    apache_path = '/etc/apache2/sites-enabled/'
    command = f'ls {apache_path}'

    # Split commands with shlex
    commands = shlex.split(command)

    # Call commands with subprocess
    process = subprocess.run(commands, capture_output=True, text=True)

    try:

        # Get the result
        result = process.stdout

        # Use regex to filter out result
        results = re.findall(r'.+.conf', result)

        # Remove ssl configurations
        file_names = [i for i in results if 'le-ssl' not in i]

        # Set the results down
        results_list = []

        # Loop through file results
        for file in file_names:
            # Open file conf in result and parse out ServerName and Log file name
            command = f'cat {apache_path}{file}'

            # Split commands with shlex
            commands = shlex.split(command)

            # Call commands with subprocess
            process = subprocess.run(commands, capture_output=True, text=True)

            # Get the contents of the file
            text = process.stdout

            # Use regex to get the log name
            result = re.search(r'/.+.log', text)
            log_name = result.group().lstrip("/")

            # Re to match server name line in to groups
            result = re.search(r'(ServerName)\s(.*)', text)

            # Get the group for the values of server name line
            urls_ips = result.groups()[1]

            # Get ips in the value from urls_ips
            ips = re.findall( r'[0-9]+(?:\.[0-9]+){3}', urls_ips)
            
            # Remove ips from the list
            urls_ips = urls_ips.split()

            for i in ips:
                urls_ips.remove(i)
            
            # Get one link out of urls_ips
            link = urls_ips[0]

            
            # Arrange data in a dict and append to results_list
            data = {
                'file_name': file,
                'log': log_name,
                'url': link,
            }

            results_list.append(data)


        return results_list

    except Exception as e:
        logger.debug(f'Error while trying to get directory list for {apache_path}')
        err_logger.exception(e)

    return ''


# Function to convert errors from django format to linode format
def convert_error(data=None):
    if data is None:
        data = dict()

    # Set list of errors
    processed_errors = []
    
    try:
        errors = data.get('errors')
        # Is error a dict
        if isinstance(errors, dict):

            # Loop through data to create this
            # {'reason': 'value', 'field': 'key'}
            for key, value in errors.items():
                # Value would be a list of strings
                # Convert all of value to one string
                value = mark_safe('<br>'.join(value))

                new_error = {
                    'reason': value,
                    'field': key,
                }
                processed_errors.append(new_error)

            # Return the processed errors
            return {'errors': processed_errors}
    except Exception as e:
        err_logger.exception(e)


# Get if a request is an ajax request
def is_ajax(request):
    requested_html = re.search(r'^text/html', request.META.get('HTTP_ACCEPT'))
    return not requested_html


