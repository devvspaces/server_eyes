from django.urls import path
from . import views


app_name = 'panel'
urlpatterns = [
    # Github webhook
    path(
        'github/payload/',
        views.github_receive_webhook, name='github-webhook'),

    # Logged in views
    path(
        '', views.Dashboard.as_view(), name='dashboard'),

    path(
        'server/<str:slug_name>/',
        views.ServerPage.as_view(), name='server_page'),
    path(
        'server/websites/refresh/<str:slug_name>/',
        views.update_server_websites, name='websites_refresh'),
    path(
        'server/websites/recheck/<str:slug_name>/',
        views.recheck_server_websites, name='websites_recheck'),

    path(
        'services/<str:service_name>/',
        views.ServiceLog.as_view(), name='service'),
    path(
        'service/stat/<str:service_name>/',
        views.recheck_service_status, name='recheck_service'),
    path('service/logs/', views.get_logs_view, name='get_logs'),

    path(
        'server/<str:server_name>/websites/<str:conf_filename>/',
        views.WebsiteLog.as_view(), name='website'),
    path(
        'websites/recheck/<str:conf_filename>/',
        views.recheck_website_status, name='recheck_website'),
    path(
        'website/logs/<str:conf_filename>/',
        views.get_websites_logs_view, name='get_log_website'),

    path('domain/', views.DomainList.as_view(), name='domain-list'),
    path(
        'domain/update/',
        views.update_domain_list, name='domain-list-update'),
    path(
        'domain/<int:domain_id>/subdomains/',
        views.DomainDetail.as_view(), name='domain-detail'),
    path(
        'domain/<int:domain_id>/subdomains/update/',
        views.update_subdomain_list, name='subdomain-list-update'),

    path(
        'file-manager/',
        views.FileManagerView.as_view(), name='file-manager'),


    # Github
    path(
        'github/accounts/',
        views.GithubAccountList.as_view(), name='github_list'),
    path(
        'github/accounts/create/',
        views.GithubAccountCreate.as_view(), name='github_account_create'),
    path(
        'github/accounts/<str:username>/',
        views.GithubAccountDetail.as_view(), name='github_detail'),
    path(
        'github/accounts/update-accounts/<str:username>/',
        views.update_github_accounts, name='update_github_accounts'),
    path(
        'github/accounts/update/<str:username>/',
        views.GithubAccountUpdate.as_view(), name='github_update'),
    path(
        'github/accounts/delete/<str:username>/',
        views.delete_github_account, name='github_delete'),

    path(
        'github/accounts/update/<str:username>/user/<str:account_name>/',
        views.GithubAccountUserUpdate.as_view(), name='github_update_user'),
    path(
        'github/accounts/update/<str:username>/user/repository/<str:account_name>/',  # noqa
        views.update_repos, name='update_repos'),
]
