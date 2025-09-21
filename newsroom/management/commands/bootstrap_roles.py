from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from newsroom.models import Article, User


class Command(BaseCommand):
    help = "Create Reader, Editor, Journalist groups with permissions"

    def handle(self, *args, **options):
        article_ct = ContentType.objects.get_for_model(Article)
        reader_group, _ = Group.objects.get_or_create(name='Reader')
        editor_group, _ = Group.objects.get_or_create(name='Editor')
        journalist_group, _ = Group.objects.get_or_create(name='Journalist')

        # Clear any old perms
        for g in (reader_group, editor_group, journalist_group):
            g.permissions.clear()
        view_article = Permission.objects.get(
            codename='view_article', content_type=article_ct)
        add_article = Permission.objects.get(
            codename='add_article', content_type=article_ct)
        change_article = Permission.objects.get(
            codename='change_article', content_type=article_ct)
        delete_article = Permission.objects.get(
            codename='delete_article', content_type=article_ct)
        approve_article = Permission.objects.get(
            codename='can_approve', content_type=article_ct)

        # Assign
        reader_group.permissions.add(view_article)
        editor_group.permissions.add(
            view_article, change_article, delete_article, approve_article)
        journalist_group.permissions.add(
            view_article, add_article, change_article, delete_article)

        self.stdout.write(self.style.SUCCESS(
            'Groups and permissions bootstrapped.'))
