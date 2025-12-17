from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),
    path('authorize/', views.auth, name='auth'),
    path('dummy_par_endpoint/', views.dummy_par_endpoint, name="dummy_par_endpoint")
]