"""
Management command: sync_tasks

Scans all registered DRF ViewSets via the URL resolver and ensures a Task row
exists in the database for every  "{basename}.{action}"  codename.

Usage:
    python manage.py sync_tasks             # create missing Task rows
    python manage.py sync_tasks --dry-run   # preview without writing
"""
from django.core.management.base import BaseCommand
from django.urls import get_resolver, URLPattern, URLResolver
from rest_framework.viewsets import ViewSetMixin

# Standard DRF router actions that every ModelViewSet can expose.
_STANDARD_ACTIONS = ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']


def _collect_viewsets(resolver, seen_basenames=None):
    """
    Walk the URL resolver tree and return a dict of {basename: viewset_class}.
    Only the first occurrence of each basename is kept (routers register each
    basename once, but the URL tree may have multiple patterns per route).
    """
    if seen_basenames is None:
        seen_basenames = {}

    for pattern in resolver.url_patterns:
        if isinstance(pattern, URLResolver):
            _collect_viewsets(pattern, seen_basenames)
        elif isinstance(pattern, URLPattern):
            cb = pattern.callback
            cls = getattr(cb, 'cls', None)
            if cls is None or not (isinstance(cls, type) and issubclass(cls, ViewSetMixin)):
                continue
            initkwargs = getattr(cb, 'initkwargs', {})
            basename = initkwargs.get('basename')
            if basename and basename not in seen_basenames:
                seen_basenames[basename] = cls

    return seen_basenames


class Command(BaseCommand):
    help = 'Sync ViewSet endpoints → Task rows so they are visible in Django admin for RoleTask assignment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without writing to the database',
        )

    def handle(self, *args, **options):
        from user_management.models import Task

        dry_run: bool = options['dry_run']

        resolver = get_resolver()
        viewsets = _collect_viewsets(resolver)

        if not viewsets:
            self.stdout.write(self.style.WARNING('No ViewSets found — is the URL conf loaded correctly?'))
            return

        created = 0
        existed = 0

        for basename, viewset_cls in sorted(viewsets.items()):
            actions = set()

            # CRUD actions that the viewset actually implements
            for action_name in _STANDARD_ACTIONS:
                if hasattr(viewset_cls, action_name):
                    actions.add(action_name)

            # Custom @action decorators exposed via get_extra_actions()
            for extra in viewset_cls.get_extra_actions():
                actions.add(extra.__name__)

            for action_name in sorted(actions):
                codename = f'{basename}.{action_name}'
                name = f'{basename} {action_name}'.replace('_', ' ').title()

                if dry_run:
                    self.stdout.write(f'  [dry-run] {codename}')
                    continue

                _, was_created = Task.objects.get_or_create(
                    codename=codename,
                    defaults={'name': name},
                )
                if was_created:
                    created += 1
                    self.stdout.write(self.style.SUCCESS(f'  + {codename}'))
                else:
                    existed += 1

        if dry_run:
            self.stdout.write('\nDry run complete — nothing was written.')
        else:
            self.stdout.write(f'\nDone. Created: {created}  |  Already existed: {existed}')
