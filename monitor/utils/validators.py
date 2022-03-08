import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from utils.general import invalid_str

def validate_special_char(value):
    if invalid_str(value):
        raise ValidationError(
            _('Must not contain special characters'),
            params={'value': value},
        )

def validate_phone(phone=''):
    pattern =r'^\+(?:[0-9] ?){6,14}[0-9]$'
    s=re.match(pattern,phone)
    if s is not None:
        return True


def validate_rating_level(val):
    if val >= 1 or val <=5:
        return True


