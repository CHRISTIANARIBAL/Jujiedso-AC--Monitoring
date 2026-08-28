
from django.contrib import admin
from django.urls import path
from monitor.views import *
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard, name='dashboard'),
    path('test-broadcast/', test_broadcast, name='test_broadcast'),
    path("client-info/", client_info, name="client_info"),
    path("raw-logs/", raw_logs, name="raw_logs"),
    path("raw-logs/<str:ac_name>/<str:filename>/", raw_log_viewer, name="raw_log_viewer"),
    path("client-search/", client_search, name="client_search"),
    path("login/", auth_views.LoginView.as_view(template_name="monitor/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("client-traffic/", client_traffic, name="client_traffic"),
    # path("pppoe-live-traffic/", pppoe_live_traffic, name="pppoe_live_traffic"),
]
