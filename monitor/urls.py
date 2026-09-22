
from django.contrib import admin
from django.urls import path, include
from monitor.views import *
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("client-traffic/", client_traffic_history, name="client_traffic"),
]