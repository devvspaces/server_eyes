from django.urls import path

from . import views

app_name = 'deploy'
urlpatterns = [
    path('react/', views.ReactDeployedApps.as_view(), name='react'),
    path('react/new/', views.ReactDeployNewapp.as_view(), name='react-new')
]
