from django.urls import path
from . import views


app_name = 'panel'
urlpatterns = [
    path('',  views.login_view, name='login'),
    path('logout/',  views.logout_view, name='logout'),

    # Logged in views
    path('app/dashboard/',  views.Dashboard.as_view(), name='dashboard'),
]