from typing import Union
from .linode import LinodeClient
from .base_api import BaseAbstractDNS

DnsType = Union[LinodeClient, BaseAbstractDNS]
