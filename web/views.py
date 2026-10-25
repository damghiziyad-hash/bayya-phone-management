from django.conf import settings
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
from django.views.i18n import set_language

from accounts.models import User

from .services import get_dashboard_stats


class LoginView(auth_views.LoginView):
    """Connexion Django standard (hachage, CSRF, validation de `next`).
    Ajout : applique la langue préférée de l'utilisateur à la connexion."""

    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        language = form.get_user().preferred_language
        if language in dict(settings.LANGUAGES):
            response.set_cookie(
                settings.LANGUAGE_COOKIE_NAME, language,
                max_age=settings.LANGUAGE_COOKIE_AGE, path=settings.LANGUAGE_COOKIE_PATH,
                domain=settings.LANGUAGE_COOKIE_DOMAIN, secure=settings.LANGUAGE_COOKIE_SECURE,
                httponly=settings.LANGUAGE_COOKIE_HTTPONLY, samesite=settings.LANGUAGE_COOKIE_SAMESITE,
            )
        return response


@require_POST
def switch_language(request):
    """Change la langue (cookie, pour tous les visiteurs) via la vue Django `set_language`,
    puis mémorise le choix dans le profil si l'utilisateur est connecté."""
    response = set_language(request)
    language = request.POST.get("language")
    if request.user.is_authenticated and language in dict(settings.LANGUAGES):
        # update() plutôt que save() : évite de relancer la synchronisation des groupes.
        User.objects.filter(pk=request.user.pk).update(preferred_language=language)
    return response


class DashboardView(PermissionRequiredMixin, TemplateView):
    # Anonyme -> redirection vers la connexion ; connecté sans droit -> 403.
    permission_required = "catalog.view_product"
    template_name = "web/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stats"] = get_dashboard_stats(self.request.user)
        context["currency"] = getattr(settings, "STORE_CURRENCY", "MAD")  # hypothèse : MAD
        return context
