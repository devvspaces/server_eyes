from django.urls import path

from . import views

app_name = 'deploy'
urlpatterns = [
    path('react/', views.ReactDeployedApps.as_view(), name='react'),
    path('react/new/', views.ReactDeployNewapp.as_view(), name='react-new'),
    path('react/app/<str:slug>/', views.DeployDetail.as_view(), name='react-app'),
    path('react/deploy/app/<str:slug>/', views.deploy_app, name='deploy-react-app'),
    path('react/deploy/log/<str:slug>/', views.FetchDeployLog.as_view(), name='deploy-app-logs'),
]
