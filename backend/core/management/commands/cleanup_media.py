from django.core.management.base import BaseCommand
from backend.core.media import cleanup
from backend.core.models import ListeningAttempt
from datetime import timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = "Retry private file deletion and clear abandoned uploads older than one day."

    def handle(self, *args, **options):
        cleanup()
        ListeningAttempt.objects.filter(
            status="active", last_at__lt=timezone.now() - timedelta(hours=24)
        ).update(status="cancelled")
        self.stdout.write("Media cleanup and listening attempt expiry completed.")
