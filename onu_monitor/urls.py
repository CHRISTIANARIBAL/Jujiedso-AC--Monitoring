from django.urls import path
from . import views

app_name = 'onu_monitor'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/olts/', views.get_olts, name='get_olts'),
    path('api/lookup/', views.lookup, name='lookup'),
]