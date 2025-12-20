from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),
    path('authorize/', views.auth, name='auth'),
    path('dummy_token_endpoint/', views.dummy_token_endpoint, name="dummy_token_endpoint")
]