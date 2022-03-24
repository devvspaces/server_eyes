from .base import *

ALLOWED_HOSTS = ['172.105.43.50', 'epanel.spacepen.tech']


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': config("DB_NAME"),
        'USER': config("DB_USER"),
        'PASSWORD': config("DB_PASSWORD"),
        'HOST': 'localhost',
        'PORT': '',
    }
}


STATIC_ROOT = os.path.join(BASE_DIR, "static")

PRINT_LOG = False
OFF_EMAIL = False


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



LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'loggers': {
        'basic': {
            'handlers': ['basic_h'],
            'level': 'DEBUG',
        },
        'basic.error': {
            'handlers': ['basic_e'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
    'handlers': {
        'basic_h': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/home/team/server_eyes/monitor/logs/debug.log',
            'formatter' : 'simple',
        },
        'basic_e': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': '/home/team/server_eyes/monitor/logs/error.log',
            'formatter' : 'simple',
        },
    },
    'formatters':{
        'simple': {
            'format': '{levelname} : {asctime} : {message}',
            'style': '{',
        }
    }
}

# Register cron jobs
CRONJOBS = [
    ('* * * * *', 'panel.cron.recheck_websites')
]