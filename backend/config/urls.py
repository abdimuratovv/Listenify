from django.urls import path, re_path
from backend.core import views

urlpatterns = [path("api/<path:route>", views.api), re_path(r"^(?!api/).*$", views.frontend)]
