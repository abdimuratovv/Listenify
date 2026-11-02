import io
import json
import tempfile
import uuid
import wave
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from backend.core.models import (
    User,
    Classroom,
    Material,
    MaterialVersion,
    PersonalLevelBlock,
    AuthSession,
    GroupLevelBlock,
    ListeningResult,
    Recording,
    Review,
    FileCleanupJob,
)
from backend.core import listening, media
from backend.core.policy import Problem, blocked_levels


def wav_bytes(seconds=1):
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16000)
        audio.writeframes(b"\0\0" * int(16000 * seconds))
    return buffer.getvalue()


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class DomainTest(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            "student@example.test", "S3cure-long-test!", name="Student"
        )
        self.other = User.objects.create_user(
            "other@example.test", "S3cure-long-test!", name="Other"
        )
        self.admin = User.objects.create_superuser(
            "admin@example.test", "S3cure-long-test!", name="Teacher"
        )
        self.material = Material.objects.create(title="Test audio", status="published")
        self.version = MaterialVersion.objects.create(
            material=self.material,
            number=1,
            level="A1-A2",
            script="Test script",
            file_key="test.media",
            mime="audio/wav",
            duration=4,
        )
        self.material.current_version = self.version
        self.material.save()
        self.client.force_login(self.student)
        session = self.client.session
        session["generation"] = 0
        session.save()
        self.tmp = tempfile.TemporaryDirectory()
        self.override = override_settings(PRIVATE_ROOT=Path(self.tmp.name))
        self.override.enable()
        Path(self.tmp.name, "test.media").write_bytes(wav_bytes(4))
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(self.override.disable)

    def as_admin(self):
        self.client.force_login(self.admin)
        session = self.client.session
        session["generation"] = 0
        session.save()

    def post(self, route, data, method="post"):
        return getattr(self.client, method)(
            "/api/" + route, json.dumps(data), content_type="application/json"
        )

    def record(self, user=None, status="saved"):
        return Recording.objects.create(
            user=user or self.student,
            version=self.version,
            file_key=uuid.uuid4().hex + ".media",
            mime="audio/wav",
            duration=1,
            digest="a" * 64,
            upload_key=uuid.uuid4(),
            status=status,
        )

    def attempt(self):
        now = timezone.now()
        attempt = listening.start(self.student, self.version, "session", now)
        return attempt, now

    def event(self, attempt, now, seq, position, event="tick"):
        result = listening.heartbeat(
            self.student,
            attempt.pk,
            "session",
            {"sequence": seq, "position": position, "event": event},
            now,
        )
        if isinstance(result, Problem):
            raise result
        return result

    def test_full_play_pause_and_idempotent_finish(self):
        attempt, now = self.attempt()
        self.event(attempt, now, 1, 0, "play")
        self.event(attempt, now + timedelta(seconds=2), 2, 2, "pause")
        self.event(attempt, now + timedelta(seconds=4), 3, 2, "play")
        self.event(attempt, now + timedelta(seconds=6), 4, 4, "ended")
        with patch("backend.core.listening.timezone.now", return_value=now + timedelta(seconds=6)):
            self.assertEqual(listening.finish(self.student, attempt.pk, "session"), 1)
            self.assertEqual(listening.finish(self.student, attempt.pk, "session"), 1)

    def test_short_play_and_seek_do_not_count(self):
        attempt, now = self.attempt()
        self.event(attempt, now, 1, 0, "play")
        self.event(attempt, now + timedelta(seconds=0.2), 2, 0.2)
        self.event(attempt, now + timedelta(seconds=0.21), 3, 3.9, "seek")
        self.event(attempt, now + timedelta(seconds=0.22), 4, 3.9, "play")
        self.event(attempt, now + timedelta(seconds=0.32), 5, 4, "ended")
        with self.assertRaises(Problem):
            listening.finish(self.student, attempt.pk, "session")
        self.assertFalse(ListeningResult.objects.exists())

    def test_forged_elapsed_time_cancels_attempt(self):
        attempt, now = self.attempt()
        self.event(attempt, now, 1, 0, "play")
        with self.assertRaises(Problem):
            self.event(attempt, now + timedelta(seconds=0.1), 2, 4, "ended")
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, "cancelled")

    def test_tolerance_is_total_not_per_event(self):
        attempt, now = self.attempt()
        self.event(attempt, now, 1, 0, "play")
        self.event(attempt, now + timedelta(seconds=1), 2, 1.2)
        with self.assertRaises(Problem):
            self.event(attempt, now + timedelta(seconds=2), 3, 2.4)

    def test_multiple_small_gaps_exceed_total_coverage_tolerance(self):
        attempt, now = self.attempt()
        self.event(attempt, now, 1, 0, "play")
        self.event(attempt, now + timedelta(seconds=1), 2, 1)
        self.event(attempt, now + timedelta(seconds=1.01), 3, 1.15, "seek")
        self.event(attempt, now + timedelta(seconds=1.02), 4, 1.15, "play")
        self.event(attempt, now + timedelta(seconds=2.02), 5, 2.15)
        self.event(attempt, now + timedelta(seconds=2.03), 6, 2.3, "seek")
        self.event(attempt, now + timedelta(seconds=2.04), 7, 2.3, "play")
        self.event(attempt, now + timedelta(seconds=3.74), 8, 4, "ended")
        with self.assertRaises(Problem):
            listening.finish(self.student, attempt.pk, "session")

    def test_seek_back_then_fill_gap_counts(self):
        attempt, now = self.attempt()
        events = [
            (0, 0, "play"),
            (2, 2, "tick"),
            (2.01, 3, "seek"),
            (2.02, 3, "play"),
            (3.02, 4, "ended"),
            (3.03, 2, "seek"),
            (3.04, 2, "play"),
            (5.04, 4, "ended"),
        ]
        for seq, (elapsed, position, event) in enumerate(events, 1):
            self.event(attempt, now + timedelta(seconds=elapsed), seq, position, event)
        with patch(
            "backend.core.listening.timezone.now", return_value=now + timedelta(seconds=5.04)
        ):
            self.assertEqual(listening.finish(self.student, attempt.pk, "session"), 1)

    def test_parallel_start_supersedes_and_duplicate_sequence_cancels(self):
        attempt, now = self.attempt()
        listening.start(self.student, self.version, "other-tab", now)
        with self.assertRaises(Problem):
            self.event(attempt, now, 1, 0, "play")
        current, now = self.attempt()
        self.event(current, now, 1, 0, "play")
        with self.assertRaises(Problem):
            self.event(current, now, 1, 0, "play")

    def test_timeout_and_wrong_session(self):
        attempt, now = self.attempt()
        with self.assertRaises(Problem):
            listening.finish(self.student, attempt.pk, "wrong")
        self.event(attempt, now, 1, 0, "play")
        with self.assertRaises(Problem):
            self.event(attempt, now + timedelta(seconds=6), 2, 4, "ended")

    def test_cancel_is_session_scoped_and_prevents_resuming(self):
        key = self.client.session.session_key
        attempt = listening.start(self.student, self.version, key)
        other = Client()
        other.force_login(self.student)
        session = other.session
        session["generation"] = 0
        session.save()
        self.assertEqual(other.post(f"/api/attempts/{attempt.pk}/cancel").status_code, 200)
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, "active")
        self.assertEqual(self.post(f"attempts/{attempt.pk}/cancel", {}).status_code, 200)
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, "cancelled")
        result = self.post(
            f"attempts/{attempt.pk}/heartbeat", {"sequence": 1, "position": 0, "event": "play"}
        )
        self.assertEqual(result.status_code, 409)

    def test_stale_paused_attempt_is_cancelled(self):
        attempt, now = self.attempt()
        result = listening.heartbeat(
            self.student,
            attempt.pk,
            "session",
            {"sequence": 1, "position": 0, "event": "play"},
            now + timedelta(hours=25),
        )
        self.assertIsInstance(result, Problem)
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, "cancelled")

    def test_logout_cancels_attempts_for_the_current_session(self):
        key = self.client.session.session_key
        attempt = listening.start(self.student, self.version, key)
        response = self.post("auth/logout", {})
        self.assertEqual(response.status_code, 200)
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, "cancelled")

    def test_long_pause_is_allowed_and_not_credited(self):
        attempt, now = self.attempt()
        self.event(attempt, now, 1, 0, "play")
        self.event(attempt, now + timedelta(seconds=1), 2, 1, "pause")
        self.event(attempt, now + timedelta(seconds=61), 3, 1, "play")
        result = self.event(attempt, now + timedelta(seconds=64), 4, 4, "ended")
        self.assertEqual(result.wall_time, 4)
        with patch("backend.core.listening.timezone.now", return_value=now + timedelta(seconds=64)):
            self.assertEqual(listening.finish(self.student, attempt.pk, "session"), 1)

    def test_effective_restrictions_and_direct_media(self):
        group = Classroom.objects.create(name="Class A")
        self.student.group = group
        self.student.save()
        PersonalLevelBlock.objects.create(user=self.student, level="B1-B2")
        GroupLevelBlock.objects.create(group=group, level="A1-A2")
        self.assertEqual(blocked_levels(self.student), {"A1-A2", "B1-B2"})
        self.assertEqual(self.client.get(f"/api/versions/{self.version.pk}/media").status_code, 403)
        self.assertEqual(self.client.get(f"/api/materials/{self.material.pk}").status_code, 403)
        self.assertEqual(self.post(f"versions/{self.version.pk}/attempts", {}).status_code, 403)

    def test_start_rechecks_group_after_user_was_moved(self):
        group = Classroom.objects.create(name="Restricted group")
        GroupLevelBlock.objects.create(group=group, level="A1-A2")
        # Simulate a request that loaded the user before an admin transfer committed.
        User.objects.filter(pk=self.student.pk).update(group=group)
        with self.assertRaises(Problem):
            listening.start(self.student, self.version, "session")

    def test_start_rechecks_material_after_archive(self):
        # The request's version and material objects can predate the archive action.
        Material.objects.filter(pk=self.material.pk).update(status="archived")
        with self.assertRaises(Problem):
            listening.start(self.student, self.version, "session")

    def test_transfer_preserves_recordings_reviews_counts_and_personal_blocks(self):
        record = self.record(status="graded")
        Review.objects.create(
            recording=record,
            score=4,
            comment="Good",
            reviewer=self.admin,
            reviewer_name="Teacher",
            editor=self.admin,
        )
        ListeningResult.objects.create(user=self.student, version=self.version, count=3)
        PersonalLevelBlock.objects.create(user=self.student, level="C1-C2")
        group = Classroom.objects.create(name="New class")
        GroupLevelBlock.objects.create(group=group, level="A1-A2")
        self.as_admin()
        result = self.post(
            "admin/transfer", {"user_ids": [str(self.student.pk)], "group_id": group.pk}
        )
        self.assertEqual(result.status_code, 200)
        self.student.refresh_from_db()
        self.assertEqual(blocked_levels(self.student), {"A1-A2", "C1-C2"})
        self.assertEqual(ListeningResult.objects.get(user=self.student).count, 3)
        self.assertEqual(Review.objects.get(recording=record).score, 4)
        self.post("admin/transfer", {"user_ids": [str(self.student.pk)], "group_id": None})
        self.student.refresh_from_db()
        self.assertEqual(blocked_levels(self.student), {"C1-C2"})

    def test_transfer_is_atomic_for_invalid_selection(self):
        self.as_admin()
        group = Classroom.objects.create(name="New")
        result = self.post(
            "admin/transfer",
            {"user_ids": [str(self.student.pk), str(uuid.uuid4())], "group_id": group.pk},
        )
        self.assertEqual(result.status_code, 400)
        self.student.refresh_from_db()
        self.assertIsNone(self.student.group_id)

    def test_recording_is_private_and_submission_immutable(self):
        record = self.record(self.other)
        self.assertEqual(self.client.get(f"/api/recordings/{record.pk}/media").status_code, 403)
        self.assertEqual(self.client.delete(f"/api/recordings/{record.pk}").status_code, 403)
        own = self.record()
        self.assertEqual(self.post(f"recordings/{own.pk}/submit", {}).status_code, 200)
        self.assertEqual(self.post(f"recordings/{own.pk}/submit", {}).status_code, 200)
        self.assertEqual(self.client.delete(f"/api/recordings/{own.pk}").status_code, 403)

    def test_archive_keeps_recording_access_and_blocks_practice(self):
        record = self.record()
        Path(self.tmp.name, record.file_key).write_bytes(wav_bytes())
        self.material.status = "archived"
        self.material.save()
        response = self.client.get(f"/api/recordings/{record.pk}/media")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b"".join(response.streaming_content))
        self.assertEqual(self.client.get(f"/api/versions/{self.version.pk}/media").status_code, 403)
        self.assertEqual(self.post(f"recordings/{record.pk}/submit", {}).status_code, 200)

    def test_review_validation_and_revision_conflict(self):
        record = self.record(status="submitted")
        self.as_admin()
        path = f"admin/recordings/{record.pk}/review"
        self.assertEqual(
            self.post(path, {"score": 6, "comment": "Good", "revision": 0}).status_code, 400
        )
        self.assertEqual(
            self.post(path, {"score": 4, "comment": " ", "revision": 0}).status_code, 400
        )
        self.assertEqual(
            self.post(path, {"score": 4, "comment": "Good", "revision": 0}).status_code, 200
        )
        first_time = Review.objects.get(recording=record).reviewed_at
        self.assertEqual(
            self.post(path, {"score": 3, "comment": "Stale", "revision": 0}).status_code, 409
        )
        self.assertEqual(
            self.post(path, {"score": 5, "comment": "Edited", "revision": 1}, "patch").status_code,
            200,
        )
        review = Review.objects.get(recording=record)
        self.assertEqual(review.revision, 2)
        self.assertEqual(review.reviewed_at, first_time)

    def test_block_invalidates_existing_sessions_after_unblock(self):
        student_client = self.client
        self.client = Client()
        self.as_admin()
        path = f"admin/users/{self.student.pk}"
        self.assertEqual(self.post(path, {"active": False}, "patch").status_code, 200)
        self.assertEqual(student_client.get("/api/materials").status_code, 401)
        self.post(path, {"active": True}, "patch")
        self.assertEqual(student_client.get("/api/materials").status_code, 401)

    def test_student_cannot_manage_users_or_choose_admin_role(self):
        self.assertEqual(self.client.get("/api/admin/users").status_code, 403)
        self.client.logout()
        response = self.post(
            "auth/register",
            {
                "email": "new@example.test",
                "name": "New",
                "password": "S3cure-long-test!",
                "role": "admin",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.get(email="new@example.test").role, "student")

    def test_range_requests_and_invalid_ranges(self):
        url = f"/api/versions/{self.version.pk}/media"
        response = self.client.get(url, HTTP_RANGE="bytes=0-31")
        self.assertEqual(response.status_code, 206)
        self.assertEqual(len(b"".join(response.streaming_content)), 32)
        self.assertEqual(self.client.get(url, HTTP_RANGE="bytes=999999999-").status_code, 416)
        response = self.client.get(url, HTTP_RANGE="bytes=-20")
        self.assertEqual(len(b"".join(response.streaming_content)), 20)

    def test_upload_validated_retry_deduplicated_and_changed_payload_rejected(self):
        key = str(uuid.uuid4())

        def upload(content):
            return self.client.post(
                "/api/recordings",
                {
                    "version_id": str(self.version.pk),
                    "upload_key": key,
                    "audio": SimpleUploadedFile("record.wav", content, "audio/wav"),
                },
            )

        response = upload(wav_bytes())
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(upload(wav_bytes()).status_code, 200)
        self.assertEqual(Recording.objects.count(), 1)
        self.assertEqual(upload(wav_bytes(2)).status_code, 409)
        self.assertEqual(upload(b"not audio").status_code, 400)

    def test_upload_is_aborted_during_multipart_parsing(self):
        from backend.core import uploads

        upload = SimpleUploadedFile("record.wav", wav_bytes(), "audio/wav")
        with patch.object(uploads, "upload_limit", return_value=100):
            response = self.client.post(
                "/api/recordings",
                {
                    "version_id": str(self.version.pk),
                    "upload_key": str(uuid.uuid4()),
                    "audio": upload,
                },
            )
        self.assertEqual(response.status_code, 413)
        self.assertFalse(Recording.objects.exists())

    def test_upload_declared_body_limit_is_checked_before_parsing(self):
        from backend.core import uploads

        upload = SimpleUploadedFile("record.wav", wav_bytes(), "audio/wav")
        with (
            patch.object(uploads, "upload_limit", return_value=1),
            patch.object(uploads, "FORM_OVERHEAD", 0),
        ):
            response = self.client.post(
                "/api/recordings",
                {
                    "version_id": str(self.version.pk),
                    "upload_key": str(uuid.uuid4()),
                    "audio": upload,
                },
            )
        self.assertEqual(response.status_code, 413)
        self.assertFalse(Recording.objects.exists())

    def test_list_queries_do_not_grow_with_number_of_users_or_materials(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        self.as_admin()
        with CaptureQueriesContext(connection) as before:
            self.assertEqual(self.client.get("/api/admin/users").status_code, 200)
        for index in range(5):
            User.objects.create_user(f"query{index}@example.test", "password", name=f"User {index}")
        with CaptureQueriesContext(connection) as after:
            self.assertEqual(self.client.get("/api/admin/users").status_code, 200)
        self.assertEqual(len(before), len(after))
        with CaptureQueriesContext(connection) as before:
            self.assertEqual(self.client.get("/api/materials").status_code, 200)
        for index in range(5):
            item = Material.objects.create(title=f"Audio {index}", status="published")
            version = MaterialVersion.objects.create(
                material=item,
                number=1,
                level="A1-A2",
                script="Script",
                file_key=f"audio{index}.media",
                mime="audio/wav",
                duration=4,
            )
            item.current_version = version
            item.save()
        with CaptureQueriesContext(connection) as after:
            self.assertEqual(self.client.get("/api/materials").status_code, 200)
        self.assertEqual(len(before), len(after))

    def test_material_version_resets_counts_and_preserves_source(self):
        ListeningResult.objects.create(user=self.student, version=self.version, count=3)
        self.as_admin()
        response = self.post(
            f"admin/materials/{self.material.pk}",
            {"title": "Renamed", "script": "New script", "level": "A1-A2", "status": "published"},
            "patch",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.material.refresh_from_db()
        self.assertEqual(self.material.current_version.number, 2)
        self.assertEqual(response.json()["count"], 0)
        self.version.refresh_from_db()
        self.assertEqual(self.version.script, "Test script")
        self.assertEqual(
            ListeningResult.objects.get(user=self.student, version=self.version).count, 3
        )

    def test_delete_user_and_cleanup_retry(self):
        record = self.record()
        path = Path(self.tmp.name, record.file_key)
        path.write_bytes(wav_bytes())
        self.as_admin()
        self.assertEqual(
            self.post(
                f"admin/users/{self.student.pk}", {"confirm_email": self.student.email}, "delete"
            ).status_code,
            200,
        )
        self.assertFalse(User.objects.filter(pk=self.student.pk).exists())
        self.assertTrue(Material.objects.filter(pk=self.material.pk).exists())
        with patch("pathlib.Path.unlink", side_effect=OSError("locked")):
            media.cleanup()
        job = FileCleanupJob.objects.get()
        self.assertEqual(job.attempts, 1)
        job.next_attempt_at = timezone.now()
        job.save()
        media.cleanup()
        self.assertFalse(path.exists())
        self.assertFalse(FileCleanupJob.objects.exists())

    def test_delete_recording_cleans_file_after_commit(self):
        record = self.record()
        path = Path(self.tmp.name, record.file_key)
        path.write_bytes(wav_bytes())
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.delete(f"/api/recordings/{record.pk}")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(path.exists())
        self.assertFalse(FileCleanupJob.objects.exists())

    def test_block_removes_login_session_from_database(self):
        student_client = Client()
        response = student_client.post(
            "/api/auth/login",
            json.dumps({"email": self.student.email, "password": "S3cure-long-test!"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(AuthSession.objects.filter(user=self.student).exists())
        self.as_admin()
        self.assertEqual(
            self.post(f"admin/users/{self.student.pk}", {"active": False}, "patch").status_code, 200
        )
        self.assertFalse(AuthSession.objects.filter(user=self.student).exists())
        self.assertEqual(student_client.get("/api/materials").status_code, 401)

    def test_csrf_required(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            "/api/auth/login",
            json.dumps({"email": self.student.email, "password": "test"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_password_reset_invalidates_sessions(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes

        response = self.post(
            "auth/reset-confirm",
            {
                "uid": urlsafe_base64_encode(force_bytes(self.student.pk)),
                "token": default_token_generator.make_token(self.student),
                "password": "An0ther-valid-password!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/api/materials").status_code, 401)
