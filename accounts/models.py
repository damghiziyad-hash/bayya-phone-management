from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group, UserManager as DjangoUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class Role(models.TextChoices):
    OWNER = "owner", _("Propriétaire / administrateur")
    STOCK_MANAGER = "stock_manager", _("Gestionnaire de stock")
    CASHIER = "cashier", _("Vendeur / caissier")


class UserManager(DjangoUserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", Role.OWNER)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """Utilisateur personnalisé. Le rôle détermine le groupe de permissions Django
    (même nom que le rôle) ; les permissions réelles sont définies dans accounts/roles.py."""

    role = models.CharField(_("rôle"), max_length=20, choices=Role.choices, default=Role.CASHIER)
    preferred_language = models.CharField(
        _("langue préférée"), max_length=5, choices=settings.LANGUAGES, default="fr"
    )
    phone = models.CharField(_("téléphone"), max_length=30, blank=True)

    objects = UserManager()

    def save(self, *args, **kwargs):
        if self.role == Role.OWNER:
            self.is_staff = True  # le propriétaire accède à l'administration
        super().save(*args, **kwargs)
        group, _created = Group.objects.get_or_create(name=self.role)
        self.groups.set([group])  # un seul groupe : celui du rôle

    @property
    def is_owner(self):
        return self.role == Role.OWNER
