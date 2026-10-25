from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from .exceptions import ImmutableRecordError


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(_("créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("modifié le"), auto_now=True)

    class Meta:
        abstract = True


class Status(models.TextChoices):
    ACTIVE = "active", _("Actif")
    ARCHIVED = "archived", _("Archivé")


class AuditLog(models.Model):
    """Journal d'audit en ajout seul : jamais modifié, jamais supprimé."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )
    action = models.CharField(max_length=64, db_index=True)
    object_type = models.CharField(max_length=64, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        default_permissions = ("view",)

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M} {self.action}"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ImmutableRecordError("Le journal d'audit ne peut pas être modifié.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ImmutableRecordError("Le journal d'audit ne peut pas être supprimé.")
