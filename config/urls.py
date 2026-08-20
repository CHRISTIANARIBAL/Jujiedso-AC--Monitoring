
from django.contrib import admin
from django.urls import path
from monitor.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard, name='dashboard'),
    path('test-broadcast/', test_broadcast, name='test_broadcast'),
    path("client-info/", client_info, name="client_info"),
    path("raw-logs/", raw_logs, name="raw_logs"),
    path("raw-logs/<str:ac_name>/<str:filename>/", raw_log_viewer, name="raw_log_viewer"),
    path("client-search/", client_search, name="client_search"),

]
