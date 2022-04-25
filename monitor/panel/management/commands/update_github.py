import json

from django.core.management.base import BaseCommand, CommandError

from deployer.models import Repository

from utils.general import githubClient
from utils.logger import logger, err_logger


class Command(BaseCommand):
    help = 'Loading in repositories to DB'

    def handle(self, *args, **options):
        try:
            
            # Get the repositories
            status, result = githubClient.fetch_get('repos')
            if status == 200:
                self.stdout.write(self.style.SUCCESS('Successfully loaded the repositories from GitHub'))

            # Create or Update repo list
            for repo in result:
                # Process out neccessary info like repo_id, name, full_name, clone_url, branches_url, branches
                branches_url = repo['branches_url'].rstrip('{/branch}')
                name = repo['name']

                # Get the branches
                status, result = githubClient.fetch_get('branches', url_values={'-repo-': name})

                if status == 200:

                    # Save the branches to a string
                    branches = ','.join([ branch['name'] for branch in result ])
                
                    data = {
                        'repo_id': repo['id'],
                        'name': name,
                        'full_name': repo['full_name'],
                        'clone_url': repo['clone_url'],
                        'branches_url': branches_url,
                        'branches': branches,
                    }

                    Repository.objects.update_or_create(**data)
                    self.stdout.write(self.style.SUCCESS(f'Added or Updated {data["name"]}'))

            self.stdout.write(self.style.SUCCESS('Completed Successfully'))
        except Exception as e:
            err_logger.exception(e)
            print(e)
            raise CommandError('Something went wrong here.')