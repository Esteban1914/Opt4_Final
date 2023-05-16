from django.urls import path
from . import views
urlpatterns = [
    path('', views.redirect_process),
    path('Proceso/', views.process, name="process"),
    path('Config/', views.config, name="config"),
    path('BasePost/', views.base_post, name="base_post"),
   
]
