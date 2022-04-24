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

    path('app/dashboard/websites/<str:conf_filename>/',  views.WebsiteLog.as_view(), name='website'),
    path('app/dashboard/websites/stat/<str:conf_filename>/',  views.recheck_website_status, name='recheck_website'),
    path('app/dashboard/website/logs/',  views.get_websites_logs_view, name='get_log_website'),
    
    path('app/domain/',  views.DomainList.as_view(), name='domain-list'),
    path('app/domain/update/',  views.update_domain_list, name='domain-list-update'),
    path('app/domain/<int:domain_id>/subdomains/',  views.DomainDetail.as_view(), name='domain-detail'),
    path('app/domain/<int:domain_id>/subdomains/update/',  views.update_subdomain_list, name='subdomain-list-update'),
]