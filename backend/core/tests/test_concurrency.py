"""These tests deliberately skip SQLite: it cannot validate PostgreSQL row locks."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless
from django.db import connection, close_old_connections
from django.test import TransactionTestCase, Client
from backend.core.models import (
    User,
    Material,
    MaterialVersion,
    ListeningAttempt,
    ListeningResult,
    Recording,
    Review,
)
from backend.core import listening


@skipUnless(connection.vendor == "postgresql", "Requires real PostgreSQL row locks")
class PostgreSQLConcurrency(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "student@example.test", "Concurrent-test-42!", name="Student"
        )
        self.admin = User.objects.create_superuser(
            "teacher@example.test", "Concurrent-test-42!", name="Teacher"
        )
        material = Material.objects.create(title="Concurrent fixture", status="published")
        self.version = MaterialVersion.objects.create(
            material=material,
            number=1,
            level="A1-A2",
            script="Test",
            file_key="test.media",
            mime="audio/wav",
            duration=4,
        )
        material.current_version = self.version
        material.save()

    def parallel(self, fn):
        barrier = Barrier(2)

        def worker(index):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return fn(index)
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(worker, [0, 1]))

    def test_parallel_starts_leave_only_one_active(self):
        self.parallel(
            lambda i: (
                listening.start(User.objects.get(pk=self.user.pk), self.version, f"tab-{i}").pk
            )
        )
        self.assertEqual(
            ListeningAttempt.objects.filter(user=self.user, status="active").count(), 1
        )
        self.assertEqual(
            ListeningAttempt.objects.filter(user=self.user, status="cancelled").count(), 1
        )

    def test_parallel_finish_counts_once(self):
        attempt = listening.start(self.user, self.version, "session")
        attempt.intervals, attempt.wall_time, attempt.media_time = [[0, 4]], 4, 4
        attempt.ended = True
        attempt.save()
        results = self.parallel(
            lambda i: listening.finish(User.objects.get(pk=self.user.pk), attempt.pk, "session")
        )
        self.assertEqual(results, [1, 1])
        self.assertEqual(ListeningResult.objects.get().count, 1)

    def test_parallel_review_rejects_stale_write(self):
        import uuid
        import json

        record = Recording.objects.create(
            user=self.user,
            version=self.version,
            file_key="test.media",
            mime="audio/wav",
            duration=1,
            digest="a" * 64,
            upload_key=uuid.uuid4(),
            status="submitted",
        )
        clients = []
        for _ in range(2):
            client = Client()
            client.force_login(self.admin)
            session = client.session
            session["generation"] = 0
            session.save()
            clients.append(client)

        def grade(i):
            return (
                clients[i]
                .post(
                    f"/api/admin/recordings/{record.pk}/review",
                    json.dumps({"score": 4 + i, "comment": f"Review {i}", "revision": 0}),
                    content_type="application/json",
                )
                .status_code
            )

        self.assertEqual(sorted(self.parallel(grade)), [200, 409])
        self.assertEqual(Review.objects.count(), 1)

    def test_recording_routes_work_with_optional_review(self):
        import tempfile
        import uuid
        from pathlib import Path
        from django.test import override_settings
        from backend.core.tests.test_domain import wav_bytes

        with tempfile.TemporaryDirectory() as folder, override_settings(PRIVATE_ROOT=Path(folder)):
            key = uuid.uuid4().hex + ".media"
            Path(folder, key).write_bytes(wav_bytes())
            record = Recording.objects.create(
                user=self.user,
                version=self.version,
                file_key=key,
                mime="audio/wav",
                duration=1,
                digest="a" * 64,
                upload_key=uuid.uuid4(),
                status="saved",
            )
            client = Client()
            client.force_login(self.user)
            session = client.session
            session["generation"] = 0
            session.save()
            response = client.get(f"/api/recordings/{record.pk}/media")
            self.assertEqual(response.status_code, 200)
            self.assertTrue(b"".join(response.streaming_content))
            self.assertEqual(client.post(f"/api/recordings/{record.pk}/submit").status_code, 200)
            other = Recording.objects.create(
                user=self.user,
                version=self.version,
                file_key=uuid.uuid4().hex + ".media",
                mime="audio/wav",
                duration=1,
                digest="a" * 64,
                upload_key=uuid.uuid4(),
                status="saved",
            )
            self.assertEqual(client.delete(f"/api/recordings/{other.pk}").status_code, 200)
