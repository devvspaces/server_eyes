from django.urls import path
from . import views


app_name = 'panel'
urlpatterns = [
    path('',  views.login_view, name='login'),
    path('logout/',  views.logout_view, name='logout'),

    # Logged in views
    path('app/dashboard/',  views.Dashboard.as_view(), name='dashboard'),
    path('app/dashboard/services/<str:service_name>/',  views.ServiceLog.as_view(), name='service'),
    path('app/dashboard/service/stat/<str:service_name>/',  views.recheck_service_status, name='recheck_service'),
    path('app/dashboard/service/logs/',  views.get_logs_view, name='get_logs'),
]