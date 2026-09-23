from django.urls import path
from .views import dashboard,upload,federated,client_portal
urlpatterns=[path('',dashboard,name='hospital_dashboard'),path('upload/',upload,name='hospital_upload'),path('federated/',federated,name='hospital_federated'),path('client/<str:client_id>/',client_portal,name='hospital_client')]
