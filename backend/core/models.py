import uuid
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import AbstractUser, BaseUserManager

LEVELS = [("A1-A2", "A1–A2"), ("B1-B2", "B1–B2"), ("C1-C2", "C1–C2")]


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra):
        user = self.model(email=email.strip().lower(), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        return self.create_user(
            email, password, role="admin", is_staff=True, is_superuser=True, **extra
        )


class Classroom(models.Model):
    name = models.CharField(max_length=120)


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=120)
    role = models.CharField(
        max_length=10, choices=[("student", "Student"), ("admin", "Admin")], default="student"
    )
    group = models.ForeignKey(
        Classroom, null=True, blank=True, on_delete=models.SET_NULL, related_name="students"
    )
    session_generation = models.PositiveIntegerField(default=0)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]
    objects = UserManager()


class PersonalLevelBlock(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="level_blocks")
    level = models.CharField(max_length=5, choices=LEVELS)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "level"], name="personal_level_unique")
        ]


class AuthSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="auth_sessions")
    session = models.OneToOneField("sessions.Session", on_delete=models.CASCADE, primary_key=True)


class GroupLevelBlock(models.Model):
    group = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="level_blocks")
    level = models.CharField(max_length=5, choices=LEVELS)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["group", "level"], name="group_level_unique")
        ]


class Material(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=12,
        default="draft",
        choices=[("draft", "Draft"), ("published", "Published"), ("archived", "Archived")],
    )
    current_version = models.ForeignKey(
        "MaterialVersion", null=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)


class MaterialVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name="versions")
    number = models.PositiveIntegerField()
    level = models.CharField(max_length=5, choices=LEVELS)
    script = models.TextField()
    file_key = models.CharField(max_length=150)
    mime = models.CharField(max_length=60)
    duration = models.FloatField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["material", "number"], name="version_number_unique")
        ]


class ListeningAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    version = models.ForeignKey(MaterialVersion, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40)
    status = models.CharField(max_length=12, default="active")
    sequence = models.PositiveIntegerField(default=0)
    position = models.FloatField(default=0)
    playing = models.BooleanField(default=False)
    ended = models.BooleanField(default=False)
    intervals = models.JSONField(default=list)
    media_time = models.FloatField(default=0)
    wall_time = models.FloatField(default=0)
    last_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "version"], condition=Q(status="active"), name="one_active_attempt"
            )
        ]


class ListeningResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    version = models.ForeignKey(MaterialVersion, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "version"], name="one_listening_result")
        ]


class Recording(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recordings")
    version = models.ForeignKey(MaterialVersion, on_delete=models.PROTECT)
    file_key = models.CharField(max_length=150)
    mime = models.CharField(max_length=60)
    duration = models.FloatField()
    digest = models.CharField(max_length=64)
    upload_key = models.UUIDField()
    status = models.CharField(max_length=12, default="saved")
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "upload_key"], name="upload_idempotency")
        ]


class Review(models.Model):
    recording = models.OneToOneField(Recording, on_delete=models.CASCADE, related_name="review")
    score = models.PositiveSmallIntegerField()
    comment = models.TextField()
    reviewer = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="+")
    reviewer_name = models.CharField(max_length=120)
    reviewed_at = models.DateTimeField(auto_now_add=True)
    editor = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="+")
    editor_name = models.CharField(max_length=120)
    edited_at = models.DateTimeField(auto_now=True)
    revision = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(score__gte=1, score__lte=5), name="review_score_range"
            )
        ]


class FileCleanupJob(models.Model):
    file_key = models.CharField(max_length=150, unique=True)
    attempts = models.PositiveIntegerField(default=0)
    error = models.TextField(blank=True)
    next_attempt_at = models.DateTimeField(auto_now_add=True)


class RateLimit(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    window = models.DateTimeField()
    hits = models.PositiveIntegerField(default=0)
