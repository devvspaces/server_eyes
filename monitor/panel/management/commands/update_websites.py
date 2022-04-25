import json

from django.core.management.base import BaseCommand, CommandError

from services.models import Website

from utils.general import get_enabled_sites
from utils.logger import logger, err_logger


class Command(BaseCommand):
    help = 'Loading Websites Hosted to DB'

    def handle(self, *args, **options):
        try:
            
            # Get the enabled sites
            sites = get_enabled_sites()
            self.stdout.write(self.style.SUCCESS('Successfully loaded the enabled sites'))

            # Create or Update websites list
            for data in sites:
                # Process out neccessary info like name, conf_name, log_name
                conf_name = data['file_name'].split('.')[0]
                name = conf_name.replace('_', ' ').title()
                conf_filename = conf_name

                defaults = {
                    'name': name,
                    'conf_filename': conf_filename,
                    'website_link': data['url'],
                    'log_filename': data['log']
                }

                Website.objects.update_or_create(conf_filename=conf_filename, defaults=defaults)

            self.stdout.write(self.style.SUCCESS('Completed Successfully'))
        except Exception as e:
            err_logger.exception(e)
            print(e)
            raise CommandError('Something went wrong here.')