from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from accounts.models import Role
from accounts.roles import ROLE_PERMISSIONS


class Command(BaseCommand):
    help = "Crée ou met à jour les groupes de rôles et leurs permissions (idempotent)."

    def handle(self, *args, **options):
        for role in Role.values:
            group, _created = Group.objects.get_or_create(name=role)
            if role == Role.OWNER:
                perms = Permission.objects.all()
            else:
                wanted = ROLE_PERMISSIONS.get(role, [])
                query = Q()
                for app_label, codename in wanted:
                    query |= Q(content_type__app_label=app_label, codename=codename)
                perms = Permission.objects.filter(query) if wanted else Permission.objects.none()
                if perms.count() != len(wanted):
                    found = {(p.content_type.app_label, p.codename) for p in perms}
                    missing = sorted(set(wanted) - found)
                    raise CommandError(f"Permissions introuvables pour {role}: {missing}")
            group.permissions.set(perms)
            self.stdout.write(f"{role}: {perms.count()} permission(s)")
