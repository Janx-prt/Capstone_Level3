from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from newsroom.models import Publisher, Article


class Command(BaseCommand):
    help = "Create a demo publisher, users, and three approved articles with cover images."

    def handle(self, *args, **options):
        User = get_user_model()

        # Users
        editor, _ = User.objects.get_or_create(
            username="ed",
            defaults={"email": "ed@example.com", "role": User.Roles.EDITOR},
        )
        if not editor.has_usable_password():
            editor.set_password("ed123456")
            editor.save()

        journo, _ = User.objects.get_or_create(
            username="jo",
            defaults={"email": "jo@example.com",
                      "role": User.Roles.JOURNALIST},
        )
        if not journo.has_usable_password():
            journo.set_password("jo123456")
            journo.save()

        # Publisher
        pub, _ = Publisher.objects.get_or_create(
            name="SCOOP",
            defaults={"description": "Demo publisher for landing cards"},
        )
        pub.editors.add(editor)
        pub.journalists.add(journo)

        # Three approved articles with images (Picsum gives safe demo images)
        data = [
            {
                "title": "Inside the Atelier",
                "cover_url": "https://picsum.photos/id/1011/600/800",
                "body": "A look behind the seams at modern couture.",
            },
            {
                "title": "Street Style 2025",
                "cover_url": "https://picsum.photos/id/1027/600/800",
                "body": "What the sidewalks are saying this season.",
            },
            {
                "title": "New Voices of Fashion",
                "cover_url": "https://picsum.photos/id/1005/600/800",
                "body": "Three young designers rethinking the runway.",
            },
        ]

        created = 0
        for a in data:
            _, was_created = Article.objects.get_or_create(
                title=a["title"],
                defaults={
                    "body": a["body"],
                    "cover_url": a["cover_url"],
                    "publisher": pub,
                    "author": journo,
                    "status": Article.Status.APPROVED,
                    "approved_at": timezone.now(),
                },
            )
            created += int(was_created)

        self.stdout.write(self.style.SUCCESS(
            f"Seed complete. {created} new article(s) created.\n"
            "Login as editor: ed / ed123456, journalist: jo / jo123456.\n"
            "Open http://127.0.0.1:8000/ and click a card to view details."
        ))
