from django.urls import path

from . import views

app_name = 'deploy'
urlpatterns = [
    path('react/', views.ReactDeployedApps.as_view(), name='react'),
    path('react/new/', views.ReactDeployNewapp.as_view(), name='react-new'),
    path(
        'react/app/<str:slug>/',
        views.DeployDetail.as_view(), name='react-app'),
    path(
        'react/deploy/app/<str:slug>/',
        views.deploy_app, name='deploy-react-app'),
    path(
        'react/pull/app/<str:slug>/',
        views.pull_app_repository, name='pull-app'),
    path(
        'react/deploy/log/<str:slug>/',
        views.FetchDeployLog.as_view(), name='deploy-app-logs'),
    path(
        'react/deploy/app/setup/auto-redeploy/<str:slug>/',
        views.setup_auto_redeploy_app, name='setup-redeploy'),
]
