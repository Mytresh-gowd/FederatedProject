from django.urls import path
from .views import dashboard,predict,history
urlpatterns=[path('',dashboard,name='patient_dashboard'),path('predict/',predict,name='patient_predict'),path('history/',history,name='patient_history')]
