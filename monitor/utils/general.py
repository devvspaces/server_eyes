import hmac, hashlib
import json, subprocess, os, re, shlex, requests, logging, requests, socket, datetime
from typing import List, Tuple
from cryptography.fernet import Fernet, InvalidToken

from django.core.exceptions import ObjectDoesNotExist

from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django.conf import settings


from .paramiko_wrapper import SshClient, Dir, ExcecuteError

from .logger import *





# Function used to update model objects
def update_obj(obj, fields:dict):
    for key,value in fields.items():
        setattr(obj, key, value)
    obj.save()

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

        self.endpoints = dict()

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


    def fetch_post(self, method='post', endpoint='', data=None, url_values=None, files=None) -> Tuple[int, dict]:
        # Get the endpoint
        url = self.build_uri(endpoint, url_values)

        print('Called post request', self.__class__.__name__, endpoint)

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


    def fetch_get(self, endpoint='', params:dict=None, url_values:dict=None) -> Tuple[int, dict]:
        # Get the endpoint
        url = self.build_uri(endpoint, url_values)

        print('Called get request', self.__class__.__name__, endpoint)

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
    def __init__(self, password:str=''):
        # Call BaseAPIClient init
        super().__init__()

        # Add the personal access token gotten from github here
        # Set the github api version here
        git_api_version = settings.GITHUB_API_VERSION
        self.personal_access_token = password
        self.headers = {
            'Authorization': f'Token {self.personal_access_token}',
            "Accept" : f"application/vnd.github.v{git_api_version}+json",
        }
        
        self.domain = f"https://api.github.com"

        self.endpoints = {
            'orgs': '/user/orgs',
            'repos': f'/-type-/-owner-/repos',
            'create-webhook': f'/repos/-owner-/-repo-/hooks',
            'delete-webhook': f'/repos/-owner-/-repo-/hooks/-hook_id-',
            'branches': f'/repos/-owner-/-repo-/branches',
            'user': '/user',
        }



def fetch_github_account_users(github_account) -> list:
    # Decrypt password
    password = cryptor.decrypt(github_account.password)
    
    # Init github client
    client = GithubClient(password=password)

    status, organizations = client.fetch_get('orgs')

    if status == 200:
        # Get names all oranizations
        organization_names = [org['login'] for org in organizations]

        return organization_names
    
    return list()


def fetch_repository_for_github(github_user_account) -> List[dict]:
    # Set result list
    result_list = []

    # Decrypt password
    password = cryptor.decrypt(github_user_account.account.password)
    
    # Init github client
    client = GithubClient(password=password)

    # Set the owner for this request
    owner = github_user_account.user
    if owner == 'personal':
        owner = github_user_account.account.username

    # Set url_values for user account
    url_values = {
        '-type-': github_user_account.get_owner_type_display(),
        '-owner-': owner
    }

    status, result = client.fetch_get('repos', url_values=url_values)

    if status == 200:
        # Create or Update repo list
        for repo in result:
            # Process out neccessary info like repo_id, name, full_name, clone_url, branches_url, branches, private
            branches_url = repo['branches_url'].rstrip('{/branch}')
            name = repo['name']
            full_name = repo['full_name']
            id = repo['id']
            clone_url = repo['clone_url']
            private = repo['private']
            default_branch = repo['default_branch']


            # Check if user account allows to get private repos
            if private and not github_user_account.show_private_repo:
                # Skip adding tis repository to result list

                # Delete repository if already added in database with repo id
                github_user_account.repository_set.filter(repo_id=id).delete()
                
                continue

            # Get the branches
            # Set url_values for user account
            url_values = {
                '-owner-': owner,
                '-repo-': name,
            }
            status, result = client.fetch_get('branches', url_values=url_values)

            if status == 200:

                # Save the branches to a string
                branches = ','.join([ branch['name'] for branch in result])
            
                data = {
                    'repo_id': id,
                    'name': name,
                    'full_name': full_name,
                    'clone_url': clone_url,
                    'branches_url': branches_url,
                    'branches': branches,
                    'private': private,
                    'default_branch': default_branch
                }

                # Check if repo already exists update else create
                # repo_object = github_user_account.repository_set.filter(repo_id = id).first()
                # if repo_object:
                #     # Update repo object
                #     update_obj(repo_object, data)
                
                # else:
                #     # Create new object
                #     github_user_account.repository_set.create(**data)

                github_user_account.repository_set.update_or_create(repo_id=id, defaults=data)
                
                result_list.append(data)
    
    return result_list


def validate_github_account(username:str, password:str) -> bool:
    # Decrypt password
    password = cryptor.decrypt(password)
    
    # Init github client
    client = GithubClient(password=password)

    status, _ = client.fetch_get('user')

    if status == 200:
        return True
    
    elif status != 401:
        logger.info(f'Password provided for account username - {username} returned status error code - {status}')

    return False



# Function to generate repository webhook secret
def fetch_repository_webhook_secret(repository):
    secret = f"{settings.GITHUB_WEBHOOK_SECRET}{repository.repo_id}"
    return secret


# Function to get website domain name
def get_domain_name(request):
    site = get_current_site(request)
    return site.domain


# Creating webhooks on repositories
def create_repository_webhook(repository, request) -> int:
    # Get password
    password = repository.github_user.account.password

    # Decrypt password
    password = cryptor.decrypt(password)
    
    # Init github client
    client = GithubClient(password=password)

    # Set the owner for this request
    owner = repository.github_user.user
    if owner == 'personal':
        owner = repository.github_user.account.username

    # Set url_values for user account
    url_values = {
        '-repo-': repository.name,
        '-owner-': owner
    }

    # Set post data
    url = get_domain_name(request)
    web_path = reverse('panel:github-webhook')
    url = f'https://{url}{web_path}'
    
    data = {
        'events': [
            'push',
        ],
        'config': {
            'url': url,
            'content_type': 'json',
            'secret': fetch_repository_webhook_secret(repository)
        }
    }

    status, result = client.fetch_post(endpoint='create-webhook', url_values=url_values, data=data)

    if status == 201:
        # Means successfully created
        hook_id = result['id']
        return hook_id




# Code to validated SHA256
def validate_payload(body:bytes, repository, signature:str):
    secret :str = fetch_repository_webhook_secret(repository)

    # Digest to get bytes
    hmac3 = hmac.new(key=secret.encode(), digestmod=hashlib.sha256)
    hmac3.update(bytes(body.decode(), encoding="utf-8"))
    value = hmac3.hexdigest()

    # Append sha256
    value = 'sha256=' + value

    return hmac.compare_digest(value, signature)



# Delete webhook
def delete_repository_webhook(repository, hook_id:int) -> bool:
    # Get password
    password = repository.github_user.account.password

    # Decrypt password
    password = cryptor.decrypt(password)
    
    # Init github client
    client = GithubClient(password=password)

    # Set the owner for this request
    owner = repository.github_user.user
    if owner == 'personal':
        owner = repository.github_user.account.username

    # Set url_values for user account
    url_values = {
        '-repo-': repository.name,
        '-owner-': owner,
        '-hook_id-': hook_id,
    }

    status, _ = client.fetch_post(method='delete', endpoint='delete-webhook', url_values=url_values)

    if status == 204:
        # Means successfully deleted
        return True



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


def add_queryset(a, b):
    return a | b



# Get server ssh client
def fetch_server_client(server) -> Tuple[SshClient, Dir]:
    host = server.ip_address
    port = 22
    username = server.username
    password = cryptor.decrypt(server.password)

    dir_obj = Dir(username)

    client = SshClient(host, port, username, password)

    return client, dir_obj



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


def get_website_logs(website, log_type:str):

    # Connect with server client
    client, dir_obj = fetch_server_client(website.server)

    # Set log path to get
    if log_type == 'access':
        # Get access log
        log_path = website.get_access_log()
    else:
        # Get error log
        log_path = website.get_error_log()

    try:
        if log_path:
            # Read log path file
            command = f'cat {log_path}'
            stdout = client.execute(command, sudo=True)

            # Replace \n with <br> tags
            logs = stdout.replace('\n', '<br><br>')

            return mark_safe(logs)
    
    except Exception as e:
        logger.debug(f'Error while trying to get website logs for {log_path}')
        err_logger.exception(e)

    finally:
        client.close()

    return 'No Logs'


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


# Code to get enabled sites for a specified server
def fetch_enabled_sites(server):

    # Connect with server client
    client, dir_obj = fetch_server_client(server)
    web_enabled_path = settings.WEB_ENABLED_PATH.get(server.web_server).get('enabled_path')
    dir_obj.cd(web_enabled_path)

    try:
        command = f'ls {dir_obj}'
        stdout = client.execute(command)

        # Set the results down
        results_list = []

        if server.web_server == 'apache':

            # Use splitlines to get file names
            results = stdout.splitlines()
            
            # Use regex to filter out result
            # results = re.findall(r'.+.conf', stdout)
        
            # Remove ssl configurations
            file_names = [i for i in results if 'le-ssl' not in i]

            # Loop through file results
            for file in file_names:
                # Open file conf in result and parse out ServerName and Log file name and get file contents
                dir_obj.cd(file)
                command = f'cat {dir_obj}'
                stdout = client.execute(command)

                # Use regex to get the log name
                log_result :List[str] = re.findall(r'\w+ .*/.+.log', stdout)

                other_logs = []
                
                # Apache2 default location on ubuntu
                apache_default_log_dir = '/var/log/apache2'
                error_log_name = ''
                access_log_name = ''

                for item in log_result:
                    try:
                        key, value = item.split(' ')
                        value = value.replace('${APACHE_LOG_DIR}', apache_default_log_dir)

                        if not error_log_name and key == 'ErrorLog':
                            error_log_name = value
                            continue
                    
                        if not access_log_name and key == 'AccessLog':
                            access_log_name = value
                            continue

                        log_dict = {
                            'name': key,
                            'location': value,
                        }
                        other_logs.append(log_dict)

                    except ValueError as e:
                        pass


                # Re to match server name line in to groups
                url_logs = re.search(r'ServerName\s(.*)', stdout)

                # Get the group for the values of server name line
                urls_ips = url_logs.groups(1)

                # # Get ips in the value from urls_ips
                # ips = re.findall( r'[0-9]+(?:\.[0-9]+){3}', urls_ips)
                
                # # Remove ips from the list
                # urls_ips = urls_ips.split()

                # for i in ips:
                #     urls_ips.remove(i)


                # Convert other_logs to json string
                other_logs = json.dumps(other_logs)

                
                # Arrange data in a dict and append to results_list
                data = {
                    'file_name': file,
                    'error_log': error_log_name,
                    'access_log': access_log_name,
                    'urls': urls_ips,
                    'other_logs': other_logs,
                }

                results_list.append(data)

                # Go back in directory to reuse dir
                dir_obj.go_back()

        elif server.web_server == 'nginx':
            # Use splitlines to get file names
            results = stdout.splitlines()

            # Loop through file results
            for file in results:
                # Open file conf in result and parse out ServerName and Log file name and get file contents
                dir_obj.cd(file)
                command = f'cat {dir_obj}'
                stdout = client.execute(command)


                # Use regex to get the access log name
                result = re.search(r'access_log (/.+.log)', stdout)
                
                access_log_name = '/var/log/nginx/access.log'
                if result:
                    access_log_name = result.group(1).lstrip("/")
                

                # Use regex to get the error log name
                result = re.search(r'error_log (/.+.log)', stdout)
                
                error_log_name = '/var/log/nginx/error.log'
                if result:
                    error_log_name = result.group(1).lstrip("/")
                    

                # Re to match server name line in to groups
                result = re.search(r'server_name\s(.*)', stdout)

                # Set default link to server ip address (FQDN) if not found in conf file
                default_link = server.ip_address
                if result:
                    # Get the group for the values of server name line
                    urls_ips = result.group(1)

                    # # Get ips in the value from urls_ips
                    # ips = re.findall( r'[0-9]+(?:\.[0-9]+){3}', urls_ips)
                    
                    # # Remove ips from the list
                    # urls_ips = urls_ips.split()

                    # for i in ips:
                    #     urls_ips.remove(i)
                    
                    # Clean urls_ips
                    cleaned_links = []
                    for _link in urls_ips:
                        _link = _link.rstrip(';')
                        clean_link = _link if _link != '_' else default_link
                        cleaned_links.append(clean_link)


                # Arrange data in a dict and append to results_list
                data = {
                    'file_name': file,
                    'error_log': error_log_name,
                    'access_log': access_log_name,
                    'urls': cleaned_links,
                }

                results_list.append(data)

                # Go back in directory to reuse dir
                dir_obj.go_back()

        return results_list

    except Exception as e:
        logger.debug(f'Error while trying to get website list for {web_enabled_path}')
        err_logger.exception(e)

    finally:
        client.close()

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
                value = "\n".join(value)
                value = mark_safe(value)

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


# Code to quickly run os commands in one line
def run_command(command, **kwargs):
    commands = shlex.split(command)
    return subprocess.run(commands, capture_output=True, text=True, **kwargs)


def update_app_status(app, status='failed'):
    app.status = status
    app.save()


# Code to get total seconds from 1970 till now
def get_total_seconds_from_start():
    now = datetime.datetime.now()
    td = (now-datetime.datetime(1970,1,1))
    return td.total_seconds()


def get_apache_conf_file(app, dir_obj:Dir):
    template = f"""
    <VirtualHost *:80>
        ServerAdmin admin@""" + f"{app.raw_link()}" + """
        ServerName """ + f"{app.raw_link()}" + """

        """ + f"DocumentRoot {dir_obj}/build" + """
        DirectoryIndex index.html

        <Directory """ + f"{dir_obj}/build" + """>
            Options Indexes FollowSymLinks MultiViews
            AllowOverride All
            Require all granted
        </Directory>

        ErrorLog ${APACHE_LOG_DIR}/""" + f"{app.slug}.error.log" + """
        CustomLog ${APACHE_LOG_DIR}/""" + f"{app.slug}.log" + """ combined

    </VirtualHost>
    """

    return template


def get_nginx_conf_file(app, dir_obj:Dir):
    template = """
        server {
            listen 80;
            listen [::]:80;
        
    """ + f"""

            root {dir_obj}/build;
            index index.html index.htm index.nginx-debian.html;

            server_name {app.raw_link()};

    """ + """

            location / {
                    try_files $uri $uri/ =404;
            }
        }
    """

    return template



loggers = {}

def myLogger(name, file:str):
    global loggers
    
    if loggers.get(name):
        return loggers.get(name)
    else:
        # Create or get log
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)


        # 1. Create handler and formatter for logger
        handler = logging.FileHandler(filename=file, mode='a')
        format = logging.Formatter(fmt="{levelname} : {asctime} : {message}", style="{")
        handler.setFormatter(format)

        # 2. Add handler to app
        logger.addHandler(handler)

        loggers[name] = logger
                       
        return logger


# Enable web server configuration
def enable_web_server(app, app_logger=None, client=None):

    # Get app server
    server = app.server
    
    # If logger is not passed get new log
    if app_logger is None:
        # Get deploy log
        log_file = app.get_log_file()

        # Create or get log
        app_logger = myLogger('appLogger', log_file)
    

    # If client is not passed establish new connection
    created_new_client = False
    if client is None:
        # Connect with server client
        client, dir_obj = fetch_server_client(server)

        # This is used to monitor whether to close client connection after done with process if client was created here
        # Else leave client closing to the user passing it
        created_new_client = True 
    
    
    try:
        # Server configuration location
        server_conf_location :str = app.get_web_server_conf()

        # First check if enabled file already exists
        possible_enabled_file_name = server_conf_location.replace('available', 'enabled')
        file_exists = client.file_exists(possible_enabled_file_name)

        if not file_exists:
            if server.web_server == 'apache':
                command = f"a2ensite {app.slug}.conf"
            elif server.web_server == 'nginx':
                command = f"ln -s {server_conf_location} /etc/nginx/sites-enabled"

            client.execute(command, sudo=True)
            app_logger.info(f'Website configuration successfully enabled')
        
        else:
            app_logger.info(f'Website configuration already successfully enabled')
        
    except Exception as e:
        app_logger.info(f'Error while trying to Enable web server')
        update_app_status(app)
        app_logger.exception(e)

    finally:
        app_logger.info('Finished Enabling server\n\n\n')

        # If client was created here make sure to close it
        if created_new_client:
            client.close()


def start_redeploy_process(app):
    
    # Get app server
    server = app.server


    # Connect with server client
    client, dir_obj = fetch_server_client(server)

    # Get deploy log
    log_file = app.get_log_file()

    # Create or get log
    app_logger = myLogger('appLogger', log_file)
    
    app_logger.info('Started new deploying process')

    # Set to app in deployment and status is pending
    app.app_in_deployment = True
    update_app_status(app, 'pending')

    try:
        # Get deploys projects folder for this app
        deploy_project_dir = app.get_app_dir()

        # Create this project dir if not already there
        command = f"mkdir -p {deploy_project_dir}"
        client.execute(command)

        # Change directory to deploys projects folder
        dir_obj.cd(deploy_project_dir)



        # 1. Get repository from app => https://github.com/ORG/REPO.git
        clone_url :str = app.repository.clone_url

        # 2. Replace https:// with https://{username}:{password}@
        github_username = app.repository.github_user.get_account_name()
        github_password = cryptor.decrypt(app.repository.github_user.account.password)

        clone_url = clone_url.replace('https://', f"https://{github_username}:{github_password}@")

        # 3. Git clone url to a app project folder
        clone_command = f"git clone {clone_url} {deploy_project_dir}"
        stdout, stderr, status = client.execute(clone_command, raise_exception=False)

        if status != 0:
            # Check if it is already clone error
            if stderr.find('already exists and is not an empty directory') != -1:
                app_logger.info(f"\nClone Output:\nRepository already cloned moving to checkout\n\n")
            else:
                raise ExcecuteError(stdout=stdout, stderr=stderr, status=status)
        else:
            app_logger.info(f"\nClone Output:\n{stdout}\n\n")
                
        app_logger.info('Cloning repository success')



        # Set branch to selected branch: If branch not there leave at default master branch
        command = f"cd {dir_obj};git checkout {app.branch}"
        stdout, stderr, status = client.execute(stdout, raise_exception=False)
        app_logger.info(f"\Checkout Output:\n{stdout}\n\n")
        app_logger.info(f"\Checkout Stderr:\n{stderr}\n\n")
        app_logger.info(f"\Checkout Status:\n{status}\n\n")
        

        # Run git pull to update branch
        command = f"cd {dir_obj};git pull {clone_url} {app.branch}"
        stdout, stderr, status = client.execute(command, raise_exception=False)
        
        if status != 0:
            raise ExcecuteError(stdout=stdout, stderr=stderr, status=status)

        # if stdout.find('Already up to date') == -1:
        app_logger.info(f"\nPull Output:\n{stdout}\n\n")
        app_logger.info(f"\nPull STDERR:\n{stderr}\n\n")

        app_logger.info(f'Git pull update on branch successfully')




        # Run npm install
        command = f"cd {dir_obj};npm install"
        stdout = client.execute(command)
        app_logger.info(f"\nNpm install Output:\n{stdout}\n\n")

        app_logger.info(f'Project dependencies installed successfully')




        # Add domain to package.json homepage key
        command = f"cat {dir_obj}/package.json"
        stdout = client.execute(command)

        # Load stdout as json
        package_json_dictionary = json.loads(stdout)

        # Check if it needs updating
        current_homepage_link = package_json_dictionary.get('homepage')
        if (current_homepage_link is None) or (current_homepage_link != app.get_link()):
            # Update it
            package_json_dictionary['homepage'] = app.get_link()

            # Set dictionary indent to 2
            new = json.dumps(package_json_dictionary, indent=2)

            # Update package.json back
            ftp = client.client.open_sftp()
            file_link = f"{dir_obj}/package.json"
            file = ftp.file(file_link, "w", -1)
            file.write(new)
            file.flush()
            ftp.close()

            command = f"cat {dir_obj}/package.json"
            stdout = client.execute(command)

            app_logger.info(f'Project package.json homepage update success')
        
        else:
            app_logger.info(f'Project package.json homepage already added')




        # Run npm build
        command = f"cd {dir_obj};npm run build"
        stdout = client.execute(command)
        app_logger.info(f"\nNpm Build Output:\n{stdout}\n\n")

        app_logger.info(f'Project build is completed')




        # Create and upload server conf
        if server.web_server == 'apache':
            template = get_apache_conf_file(app, dir_obj)
        elif server.web_server == 'nginx':
            template = get_nginx_conf_file(app, dir_obj)
        
        app_logger.info(f"\nWeb server Template Output:\n{template}\n\n")

        server_conf_location :str = app.get_web_server_conf()

        # File create file in current location and then move to webserver location with sudo
        tseconds = get_total_seconds_from_start()
        new_file_loc = f"{dir_obj}/web_server_server_eyes_7934hsohsp_location_{app.slug}_{tseconds}.config"

        ftp = client.client.open_sftp()
        file = ftp.file(new_file_loc, "w", -1)
        file.write(template)
        file.flush()
        ftp.close()

        app_logger.info(f"\nCreated server configuration file version in codebase\n\n")


        # Move created file to webserver directory
        command = f"mv {new_file_loc} {server_conf_location}"
        stdout = client.execute(command, sudo=True)
        app_logger.info(f"\nMoved server configuration file version to web server directory\n\n")

        app_logger.info(f'Completly created web server configuration')




        

        # Enable web server configuration

        # First check if enabled file already exists
        possible_enabled_file_name = server_conf_location.replace('available', 'enabled')
        file_exists = client.file_exists(possible_enabled_file_name)

        

        if not file_exists:
            if server.web_server == 'apache':
                command = f"a2ensite {app.slug}.conf"
            elif server.web_server == 'nginx':
                command = f"ln -s {server_conf_location} /etc/nginx/sites-enabled"

            stdout = client.execute(command, sudo=True)
            app_logger.info(f'Website configuration successfully enabled')
        
        else:
            app_logger.info(f'Website configuration already successfully enabled')






        # Restart webserver server
        if server.web_server == 'apache':
            command = f"systemctl restart apache2"
        elif server.web_server == 'nginx':
            command = f"systemctl restart nginx"
        
        stdout = client.execute(command, sudo=True)
        app_logger.info(f"\nWebserver Restart Output:\n{stdout}\n\n")



        
        update_app_status(app, 'deployed')
        app_logger.info(f'Website is successfully deployed.')


    except Exception as e:
        app_logger.info(f'Error while trying to deploy app directory on server')
        update_app_status(app)
        app_logger.exception(e)

    finally:
        app_logger.info('Finished Deploying\n\n\n')
        client.close()

    # Update app not more in deployment
    app.app_in_deployment = False
    app.save()