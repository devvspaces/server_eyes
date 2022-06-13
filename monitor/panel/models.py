from typing import Dict, List

from django.conf import settings
from django.db import models
from django.utils.text import slugify
from utils.general import printt as print  # noqa
from utils.process import ServerProcess
from utils.github import GithubClient
from utils.model_mixins import ModelChangeFunc


# NOTE: Create custom model field for comma separated fields


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
    server_os_name = models.CharField(max_length=100, blank=True)
    server_os_version = models.CharField(max_length=100, blank=True)
    server_os_url = models.URLField(blank=True)

    name = models.CharField(
        help_text='Unique name for identifying server',
        max_length=45, unique=True)
    slug_name = models.SlugField(unique=True, blank=True)

    # Login credentials
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=1024)

    __process: ServerProcess = None

    def create_process(self) -> ServerProcess:
        """
        Create a server process
        """

        return ServerProcess(
            host=self.ip_address,
            username=self.username,
            password=self.password,
            web_server=self.web_server
        )

    def get_process(self) -> ServerProcess:
        """
        Get a server process
        """

        if self.__process is None:
            self.__process = self.create_process()
        return self.__process

    def get_connected_process(self) -> ServerProcess:
        """
        Get a connected server process
        """

        client = self.get_process()
        client.create_client()
        return client

    def update_slug(obj):
        obj.slug_name = slugify(obj.name)

    def update_server_details(self):
        self.server_os_name = self.get_connected_process().get_server_name()
        self.server_os_version = self.get_connected_process()\
            .get_server_version()
        self.server_os_url = self.get_connected_process()\
            .get_server_os_home_url()

    monitor_change = {
        'name': update_slug,
        'ip_address': update_slug,
    }

    def __str__(self) -> str:
        return self.name

    def recheck(self):
        """
        Recheck the status of the websites
        under this server
        """

        websites = self.website_set.all()
        for website in websites:
            website.recheck()

    def get_home_directory(self):
        """
        Get server home directory
        """
        return self.get_process().get_home_directory()

    def get_enabled_sites(self) -> list:
        """
        Get enabled websites for default web server

        :return: Return enabled websites for default web server
        :rtype: _type_
        """

        client = self.get_connected_process()
        return client.fetch_enabled_sites()

    def parse_website_data(self, data: Dict[str, str]) -> dict:
        """
        Parse out the data from dictionary for website
        instance update

        :param data: Data gotten from get_enabled_sites
        :type data: Dict[str, str]
        :return: Cleaned and parsed data
        :rtype: dict
        """

        client = self.get_connected_process()
        return client.parse_website_data(data)

    def save(self, *args, **kwargs):
        if not self.server_os_name:
            self.update_server_details()
        super().save(*args, **kwargs)


class Domain(models.Model):
    """
    Domain model for top level domains
    """

    domain = models.URLField()
    domain_id = models.IntegerField(unique=True)
    status = models.CharField(max_length=50)
    status_tag = models.CharField(max_length=50)
    soa_email = models.EmailField()

    def __str__(self):
        return self.domain

    def get_subdomain_js_string(self):
        """
        Return domain subdomains and record id
        Created for deploy page js code to get domain
        names with their record id
        """

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
    """
    Subdomain model for domain A record
    """
    record_id = models.IntegerField(unique=True)
    domain_id = models.IntegerField()
    name = models.CharField(max_length=255)
    target = models.GenericIPAddressField()

    def get_name(self):
        """
        Get the subdomain name
        """

        if self.name == '.':
            return ''
        return self.name

    def __str__(self):
        return self.name


class GithubAccount(ModelChangeFunc):
    """
    Github account for users model
    """

    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(
        max_length=255,
        help_text='''Github account personal access token,
        it will be helpful if this access token will live for a long time''')

    # if any organizations are listed here they will be
    # the only oranizations that their repositories
    # can be gotten from github
    white_list_organizations = models.TextField(
        blank=True,
        help_text="""Organization names should be valid names
         and comma separated""")

    # if any organizations are listed here they will be
    # the only oranizations that their repositories
    # will not be gotten from github
    black_list_organizations = models.TextField(
        blank=True,
        help_text="""Organization names should be
        valid names and comma separated""")

    # NOTE: if white list and black list have organizations
    # listed in them, White list takes precedence over black list

    active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    # Monitor change implementations
    def update_github_accounts_white(obj):
        obj.update_account_users_whitelist()

    def update_github_accounts_black(obj):
        obj.update_account_users_blacklist()

    monitor_change = {
        'white_list_organizations': update_github_accounts_white,
        'black_list_organizations': update_github_accounts_black,
    }

    @property
    def github_client(self) -> GithubClient:
        """
        Create github client for this account
        """

        return GithubClient(self.password)

    def list_comma_field(self, field_name: str) -> list:
        """
        Get the comma separated field in the database
        as a list of items
        """

        lists = []

        field_value: str = getattr(self, field_name)
        if field_value:
            lists: List[str] = field_value.split(',')
            lists = [item.strip() for item in lists]

        return lists

    def get_white_list(self):
        """
        Get the list for whitelist
        """

        return self.list_comma_field('white_list_organizations')

    def get_black_list(self):
        """
        Get the list for blacklist
        """

        return self.list_comma_field('black_list_organizations')

    def update_account_users_blacklist(self):
        """
        Updates accounts by blacklist added
        """

        # Get oraganization names
        org_names: list = self.github_client.get_organizations_names()
        org_names.append('personal')

        black_list = self.get_black_list()
        allowed_orgs_names = list(set(org_names) - set(black_list))

        current_orgs = self.repositoryuser_set.all()
        for account in current_orgs:
            if account.user in black_list:
                account.delete()
            elif account.user in allowed_orgs_names:
                allowed_orgs_names.remove(account.user)

        # Now add new organizations
        for name in allowed_orgs_names:
            owner_type = 'personal'
            if name != 'personal':
                owner_type = 'organization'

            self.repositoryuser_set.create(
                user=name, owner_type=owner_type)

    def update_account_users_whitelist(self):
        """
        Updates accounts by whitelist added
        """

        # Get oraganization names
        org_names = self.github_client.get_organizations_names()
        org_names.append('personal')
        org_names = set(org_names)

        whitelist = set(self.get_white_list())
        allowed_orgs_names = org_names.intersection(whitelist)

        current_orgs = self.repositoryuser_set.all()
        for account in current_orgs:
            if account.user not in whitelist:
                account.delete()
            elif account.user in allowed_orgs_names:
                allowed_orgs_names.remove(account.user)

        # Now add new organizations
        for name in allowed_orgs_names:
            owner_type = 'personal'
            if name != 'personal':
                owner_type = 'organization'

            self.repositoryuser_set.create(
                user=name, owner_type=owner_type)

    def __str__(self) -> str:
        return self.username


class RepositoryUser(ModelChangeFunc):
    """
    Personal/Organization account model

    Args:
        user: to store the name of the organization
        owner_type: whether the instance is an
            organization or personal account
    """

    OWNER_TYPE = (
        ('personal', 'users',),
        ('organization', 'orgs',),
    )
    account = models.ForeignKey(GithubAccount, on_delete=models.CASCADE)
    user = models.CharField(max_length=255, default='Personal')
    owner_type = models.CharField(
        choices=OWNER_TYPE, max_length=40, default='personal')
    show_private_repo = models.BooleanField(default=False)

    # Get github account name
    def get_account_name(self) -> str:
        if self.owner_type == 'personal':
            return self.account.username

        return self.user

    # Monitor change implementations
    def update_github_account_user_repos(obj):
        """
        Update github repo when show_private_repo
        changes
        """

        obj.update_repos()

    monitor_change = {
        'show_private_repo': update_github_account_user_repos,
    }

    def get_owner(self) -> str:
        """
        Get the github owner name to use in
        api requests
        """

        owner = self.user
        if self.owner_type == 'personal':
            owner = self.account.username
        return owner

    def get_owner_type(self) -> str:
        """
        Get the owner type display
        """

        return self.get_owner_type_display()

    def update_repos(self):
        """
        Updates repositories for this github user account
        """

        client: GithubClient = self.account.github_client

        if self.show_private_repo is False:
            self.repository_set.filter(private=True).delete()

        owner = self.get_owner(),
        owner_type = self.get_owner_type()

        repository_list = client.get_repository_list(owner, owner_type)

        for repo in repository_list:
            repo_id = repo['repo_id']
            name = repo['name']
            private: bool = repo['private']

            if private and not self.show_private_repo:
                continue

            repo_branches = client.get_repository_branches(owner, name)
            branch_names = []
            for branch in repo_branches:
                branch_names.append(branch['name'])

            join_branches = ','.join(branch_names)
            repo['branches'] = join_branches

            self.repository_set.update_or_create(
                repo_id=repo_id, defaults=repo)

    def __str__(self):
        return self.user


class Repository(models.Model):
    """
    Github repository model
    """

    github_user = models.ForeignKey(RepositoryUser, on_delete=models.CASCADE)
    repo_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)
    clone_url = models.URLField()
    branches_url = models.URLField()
    branches = models.CharField(max_length=255)
    private = models.BooleanField(default=False, editable=False)
    default_branch = models.CharField(max_length=50, blank=True)

    webhook = models.BooleanField(default=False)
    hook_id = models.IntegerField(blank=True, null=True)

    def get_branches(self) -> list:
        return self.branches.split(',')

    def count_branches(self):
        return len(self.get_branches())

    @property
    def branch_count(self):
        return self.count_branches()

    def create_webhook(self, domain: str):
        """
        Create webhook for this respository
        """
        if not self.webhook:
            client: GithubClient = self.account.github_client

            hook_id = client.create_repository_webhook(
                owner=self.get_owner(),
                name=self.name,
                domain=domain,
                secret=self.get_webhook_secret()
            )
            if hook_id is not None:
                self.webhook = True
                self.hook_id = hook_id
                self.save()

    def get_owner(self) -> str:
        """
        Get repository owner username
        """

        return self.github_user.get_owner()

    def delete_webhook(self):
        """
        Delete github webhook
        """

        if self.webhook:
            client: GithubClient = self.account.github_client

            if client.delete_repository_webhook(
                owner=self.get_owner(),
                repo=self.name,
                hook_id=self.hook_id
            ):
                self.webhook = False
                self.hook_id = 0
                self.save()

    def get_webhook_secret(self):
        """
        Returns the webhook secret
        """

        return settings.GITHUB_WEBHOOK_SECRET

    def __str__(self):
        return self.name
