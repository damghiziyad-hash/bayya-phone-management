from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "web"

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="web:dashboard", permanent=False), name="root"),
    path("connexion/", views.LoginView.as_view(), name="login"),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="logout"),  # POST uniquement
    path("tableau-de-bord/", views.DashboardView.as_view(), name="dashboard"),
    path("langue/", views.switch_language, name="set_language"),
]
