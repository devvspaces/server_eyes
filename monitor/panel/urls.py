from django.urls import path
from . import views


app_name = 'panel'
urlpatterns = [
    # Github webhook
    path('github/payload/',  views.github_receive_webhook, name='github-webhook'),


    path('',  views.login_view, name='login'),
    path('logout/',  views.logout_view, name='logout'),


    # Logged in views
    path('app/dashboard/',  views.Dashboard.as_view(), name='dashboard'),

    path('app/dashboard/server/<str:slug_name>/',  views.ServerPage.as_view(), name='server_page'),
    path('app/dashboard/server/websites/refresh/<str:slug_name>/',  views.update_server_websites, name='websites_refresh'),
    path('app/dashboard/server/websites/recheck/<str:slug_name>/',  views.recheck_server_websites, name='websites_recheck'),

    path('app/dashboard/services/<str:service_name>/',  views.ServiceLog.as_view(), name='service'),
    path('app/dashboard/service/stat/<str:service_name>/',  views.recheck_service_status, name='recheck_service'),
    path('app/dashboard/service/logs/',  views.get_logs_view, name='get_logs'),

    path('app/dashboard/server/<str:server_name>/websites/<str:conf_filename>/',  views.WebsiteLog.as_view(), name='website'),
    path('app/dashboard/websites/recheck/<str:conf_filename>/',  views.recheck_website_status, name='recheck_website'),
    path('app/dashboard/website/logs/<str:conf_filename>/',  views.get_websites_logs_view, name='get_log_website'),
    
    path('app/domain/',  views.DomainList.as_view(), name='domain-list'),
    path('app/domain/update/',  views.update_domain_list, name='domain-list-update'),
    path('app/domain/<int:domain_id>/subdomains/',  views.DomainDetail.as_view(), name='domain-detail'),
    path('app/domain/<int:domain_id>/subdomains/update/',  views.update_subdomain_list, name='subdomain-list-update'),


    # Github
    path('app/dashboard/github/create/',  views.GithubAccountCreate.as_view(), name='github_account_create'),
    path('app/dashboard/github/<str:username>/',  views.GithubAccountDetail.as_view(), name='github_detail'),
    path('app/dashboard/github/update-accounts/<str:username>/',  views.update_github_accounts, name='update_github_accounts'),
    path('app/dashboard/github/update/<str:username>/',  views.GithubAccountUpdate.as_view(), name='github_update'),
    path('app/dashboard/github/delete/<str:username>/',  views.delete_github_account, name='github_delete'),

    path('app/dashboard/github/update/<str:username>/user/<str:account_name>/',  views.GithubAccountUserUpdate.as_view(), name='github_update_user'),
    path('app/dashboard/github/update/<str:username>/user/repository/<str:account_name>/',  views.update_repos, name='update_repos'),
]