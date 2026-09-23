from django.urls import path
from .views import dashboard,hospitals,patients,rounds,aggregate_round
urlpatterns=[path('',dashboard,name='admin_dashboard'),path('hospitals/',hospitals,name='admin_hospitals'),path('patients/',patients,name='admin_patients'),path('rounds/',rounds,name='admin_rounds'),path('rounds/<int:round_no>/aggregate/',aggregate_round,name='admin_aggregate_round')]
