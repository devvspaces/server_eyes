from typing import List
from django.db import models
from django.contrib.auth.models import User

from django.utils.text import slugify

from utils.general import printt as print
from utils.general import fetch_github_account_users, fetch_repository_for_github, create_repository_webhook, delete_repository_webhook
from utils.model_mixins import ModelChangeFunc


class Server(ModelChangeFunc):
    """
    Will require Server IP address for connecting to server,
    Required to select a default server implementation (nginx or apache ...)
    """
    WEB_SERVER = (
        ('apache', 'Apache'),
        ('nginx', 'Nginx'),
    )
    
    ip_address = models.GenericIPAddressField(unique=True)
    web_server = models.CharField(choices=WEB_SERVER, max_length=30)

    name = models.CharField(help_text='Unique name for identifying server', max_length=45, unique=True)
    slug_name = models.SlugField(unique=True, blank=True)

    # Login credentials
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=1024)

    def update_slug(obj):
        obj.slug_name = slugify(obj.name)

    monitor_change = {
        'name': update_slug
    }
    
    def __str__(self) -> str:
        return self.name
    
    # Recheck the status of the website
    def recheck(self):
        # Get all websites under server
        websites = self.website_set.all()
        for website in websites:
            website.recheck()
    

    # Get server home directory
    def get_home_directory(self):
        if self.username != 'root':
            return f"/home/{self.username}"
        
        return "/root"



class Domain(models.Model):
    domain = models.URLField()
    domain_id = models.IntegerField(unique=True)
    status = models.CharField(max_length=50)
    status_tag = models.CharField(max_length=50)
    soa_email = models.EmailField()

    def __str__(self):
        return self.domain
    
    def get_subdomain_js_string(self):
        # This function will be used to communicate with the deploy apps page
        # Get the subdomains
        subdomains = Subdomain.objects.filter(domain_id=self.domain_id)
        
        # Result list
        result = []

        for subdomain in subdomains:
            # Clean subdomain name
            sub_name = subdomain.name
            if sub_name:
                name = f"{sub_name}.{self.domain}"
            else:
                name = self.domain

            record_id = subdomain.record_id

            result.append(f"{name}*{record_id}")
        
        return '?'.join(result)


class Subdomain(models.Model):
    record_id = models.IntegerField(unique=True)
    domain_id = models.IntegerField()
    name = models.CharField(max_length=255)
    target = models.GenericIPAddressField()

    def get_name(self):
        if self.name == '.':
            return ''
        return self.name

    def __str__(self):
        return self.name



class GithubAccount(ModelChangeFunc):
    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255, help_text='Github account personal access token, it will be helpful if this access token will live for a long time')

    # if any organizations are listed here they will be the only oranizations that their repositories can be gotten from github
    white_list_organizations = models.TextField(blank=True, help_text="Organization names should be valid names and comma separated")
    # if any organizations are listed here they will be the only oranizations that their repositories will not be gotten from github
    black_list_organizations = models.TextField(blank=True, help_text="Organization names should be valid names and comma separated")
    # NOTE: if white list and black list have organizations listed in them, White list takes precedence over black list

    active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


    # Monitor change implementations
    def update_github_accounts(obj):
        obj.update_account_users()

    monitor_change = {
        'white_list_organizations': update_github_accounts,
        'black_list_organizations': update_github_accounts,
    }
    ####################################

    def get_white_list(self):
        if self.white_list_organizations:
            # Split white list and return list
            lists :List[str] = self.white_list_organizations.split(',')

            # Clean lists
            lists = [i.strip() for i in lists]

            return lists
    
    def get_black_list(self):
        if self.black_list_organizations:
            # Split black list and return list
            lists :List[str] = self.black_list_organizations.split(',')

            # Clean lists
            lists = [i.strip() for i in lists]

            return lists

    def update_account_users(self):
        # Get oraganization names
        org_names = fetch_github_account_users(self)

        # Add personal to the org names
        org_names.append('personal')

        # Get current organizations connected to this account
        current_orgs = self.repositoryuser_set.all()
        current_org_names = [org.user for org in current_orgs]
        
        # Check white list
        white_list = self.get_white_list()
        black_list = self.get_black_list()

        if white_list:
            # Get only names that are white listed
            # Remove accounts that are not white listed
            for name in current_org_names.copy():
                if name not in white_list:
                    current_org_names.remove(name)
            
            # Remove names that are not white listed
            for name in org_names.copy():
                if name not in white_list:
                    org_names.remove(name)
        
        elif black_list:
            # Remove only names that are black listed
            # Remove accounts that are black listed
            for name in current_org_names.copy():
                if name in black_list:
                    current_org_names.remove(name)
            
            # Remove names that are black listed
            for name in org_names.copy():
                if name in black_list:
                    org_names.remove(name)
        
        # Delete orgs that are not more in current_org_names
        for acc in current_orgs:
            if acc.user not in current_org_names:
                acc.delete()

        # Now add new organizations
        for name in org_names:
            if name not in current_org_names:
                # Set org owner type
                owner_type = 'personal' if name == 'personal' else 'organization'
                self.repositoryuser_set.create(user=name, owner_type=owner_type)

    def __str__(self) -> str:
        return self.username


class RepositoryUser(ModelChangeFunc):
    OWNER_TYPE = (
        ('personal', 'users',),
        ('organization', 'orgs',),
    )
    account = models.ForeignKey(GithubAccount, on_delete=models.CASCADE)
    user = models.CharField(max_length=255, default='Personal')
    owner_type = models.CharField(choices=OWNER_TYPE, max_length=40, default='personal')
    show_private_repo = models.BooleanField(default=False)

    # Get github account name
    def get_account_name(self) -> str:
        if self.owner_type == 'personal':
            return self.account.username

        return self.user

    # Monitor change implementations
    def update_github_account_user_repos(obj):
        obj.update_repos()

    monitor_change = {
        'show_private_repo': update_github_account_user_repos,
    }
    ####################################

    def update_repos(self):
        # Updates repositories for this github user account
        fetch_repository_for_github(self)

    def __str__(self):
        return self.user

class Repository(models.Model):
    github_user = models.ForeignKey(RepositoryUser, on_delete=models.CASCADE)
    repo_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)
    clone_url = models.URLField()
    branches_url = models.URLField()
    branches = models.CharField(max_length=255)
    private = models.BooleanField(default=False, editable=False)
    default_branch = models.CharField(max_length=50, blank=True)

    # Webhook details
    webhook = models.BooleanField(default=False)
    hook_id = models.IntegerField(blank=True, null=True)

    def get_branches(self) -> list:
        return self.branches.split(',')
    
    def count_branches(self):
        return len(self.get_branches())
    
    @property
    def branch_count(self):
        return self.count_branches()
    
    def create_webhook(self, request):
        if not self.webhook:
            # Creates github webhooks for this repo
            hook_id = create_repository_webhook(self, request)
            self.webhook = True
            self.hook_id = hook_id
            self.save()
            return True
    
    def delete_webhook(self):
        if self.webhook:
            # Delete github webhook for this repo
            result = delete_repository_webhook(self, self.hook_id)
            self.webhook = False
            self.hook_id = 0
            self.save()
            return result

    def __str__(self):
        return self.name