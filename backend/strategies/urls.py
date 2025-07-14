from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="strategies-home"),
    path("about/", views.about, name="strategies-about"),
]
