

from utils.logger import *
from services.models import Website


def recheck_websites():
    websites = Website.objects.all()

    # Loop through all websites
    for website in websites:
        # Recheck status
        website.recheck()
    
    # Log
    logger.debug(f'Completed running of cron job for reloading websites status.')
