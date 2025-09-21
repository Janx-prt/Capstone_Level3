# newsroom/management/commands/seed_roles.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from newsroom.models import Article


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        ct = ContentType.objects.get_for_model(Article)

        reader, _ = Group.objects.get_or_create(name="Reader")
        reader.permissions.set([Permission.objects.get(
            codename="view_article", content_type=ct)])

        editor, _ = Group.objects.get_or_create(name="Editor")
        editor.permissions.set([
            Permission.objects.get(codename="view_article", content_type=ct),
            Permission.objects.get(codename="change_article", content_type=ct),
            Permission.objects.get(codename="delete_article", content_type=ct),
            Permission.objects.get(codename="can_approve", content_type=ct),
        ])

        journalist, _ = Group.objects.get_or_create(name="Journalist")
        journalist.permissions.set([
            Permission.objects.get(codename="view_article", content_type=ct),
            Permission.objects.get(codename="add_article", content_type=ct),
            Permission.objects.get(codename="change_article", content_type=ct),
            Permission.objects.get(codename="delete_article", content_type=ct),
        ])
        self.stdout.write(self.style.SUCCESS("Groups & permissions seeded."))
