from django.urls import path

from . import views

app_name = "oll"

urlpatterns = [
    path("", views.index, name="index"),
]
