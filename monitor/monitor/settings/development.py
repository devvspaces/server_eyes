from .base import *

ngrok = '3467-105-112-209-212.eu.ngrok.io'
ALLOWED_HOSTS = ['*', ngrok]


EMAIL_BACKEND= 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST=config('EMAIL_HOST', default='localhost')
EMAIL_PORT= config('EMAIL_PORT', default=25, cast=int)
EMAIL_USE_SSL= config('EMAIL_USE_SSL', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
# Custom user defined mail username
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='')
DEFAULT_COMPANY_EMAIL = config('DEFAULT_COMPANY_EMAIL', default='')

TEAM_KEY = config('TEAM_KEY')


CSRF_TRUSTED_ORIGINS = [
    f'https://{ngrok}'
]