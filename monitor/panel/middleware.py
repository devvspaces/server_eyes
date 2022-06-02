from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone

from utils.logger import *

class ServerSelectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
    
    def process_exception(self, request, exception):

        logger.debug(f"Got to Middleware")

        if exception.__str__() == "SelectServerException":
            messages.success(request, "Must select a Server")
            return redirect('panel:dashboard')

        return