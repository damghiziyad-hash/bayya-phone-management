from .models import AuditLog


def log_action(user, action, obj=None, **details):
    """Enregistre une opération sensible. `details` doit être sérialisable en JSON
    (pas de Decimal, pas de secrets, pas de données personnelles inutiles)."""
    return AuditLog.objects.create(
        user=user if getattr(user, "pk", None) else None,
        action=action,
        object_type=obj._meta.label if obj is not None else "",
        object_id=str(obj.pk) if obj is not None else "",
        details=details,
    )
