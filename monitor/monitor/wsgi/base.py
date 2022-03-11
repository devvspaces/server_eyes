import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monitor.settings.production')
os.environ.setdefault('ENVIRONMENT_VARIABLE', 'monitor.settings.production')

application = get_wsgi_application()
