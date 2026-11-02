import hashlib
import json
import logging
import uuid
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sessions.models import Session
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import transaction, IntegrityError
from django.db.models import Count, IntegerField, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse, FileResponse, HttpResponse
from django.http.response import HttpResponseBase
from django.middleware.csrf import get_token
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from .models import (
    User,
    Classroom,
    PersonalLevelBlock,
    GroupLevelBlock,
    Material,
    MaterialVersion,
    Recording,
    Review,
    ListeningAttempt,
    ListeningResult,
    RateLimit,
    AuthSession,
    LEVELS,
)
from .policy import Problem, require_admin, can_practice, blocked_levels, lock_active_user
from .serializers import user_data, material_data, recording_data
from . import listening, media

logger = logging.getLogger(__name__)


def csrf_failure(request, reason=""):
    return JsonResponse({"error": "Xavfsizlik tokeni eskirgan. Sahifani yangilang."}, status=403)


def body(request):
    if request.content_type == "application/json":
        try:
            data = json.loads(request.body or "{}")
        except (ValueError, UnicodeDecodeError):
            raise Problem("JSON noto‘g‘ri.")
        if not isinstance(data, dict):
            raise Problem("JSON obyekt kerak.")
        return data
    return request.POST


def text(data, key, limit=5000):
    value = data.get(key, "")
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise Problem(f"{key}: qiymat majburiy, ko‘pi bilan {limit} belgi.")
    return value.strip()


def method(request, *allowed):
    if request.method not in allowed:
        raise Problem("HTTP usuli ruxsat etilmagan.", 405)


def throttle(request, action, identifier="", limit=10):
    # DB-backed across application processes. Do not trust arbitrary proxy headers.
    key = hashlib.sha256(
        f"{action}:{request.META.get('REMOTE_ADDR')}:{identifier}".encode()
    ).hexdigest()
    with transaction.atomic():
        row, _ = RateLimit.objects.select_for_update().get_or_create(
            key=key, defaults={"window": timezone.now()}
        )
        if timezone.now() - row.window > timedelta(minutes=15):
            row.window, row.hits = timezone.now(), 0
        row.hits += 1
        row.save()
        exceeded = row.hits > limit
    if exceeded:
        raise Problem("Juda ko‘p urinish. 15 daqiqadan so‘ng takrorlang.", 429)


def session_user(request):
    if not request.user.is_authenticated:
        raise Problem("Avval hisobingizga kiring.", 401)
    if (
        not request.user.is_active
        or request.session.get("generation") != request.user.session_generation
    ):
        logout(request)
        raise Problem("Sessiya tugatilgan. Qayta kiring.", 401)
    return request.user


def invalidate_sessions(user):
    keys = list(AuthSession.objects.filter(user=user).values_list("session_id", flat=True))
    ListeningAttempt.objects.filter(user=user, status="active").update(status="cancelled")
    Session.objects.filter(session_key__in=keys).delete()


def api(request, route):
    try:
        response = dispatch(request, route.strip("/").split("/"))
        if not isinstance(response, HttpResponseBase):
            response = JsonResponse(response, safe=not isinstance(response, list))
        response["Cache-Control"] = "private, no-store"
        return response
    except Problem as error:
        return JsonResponse({"error": error.message}, status=error.status)
    except ObjectDoesNotExist:
        return JsonResponse({"error": "Ma’lumot topilmadi."}, status=404)
    except (ValidationError, ValueError, TypeError, OverflowError):
        return JsonResponse({"error": "Kiritilgan ma’lumot noto‘g‘ri."}, status=400)
    except IntegrityError:
        return JsonResponse(
            {"error": "Ma’lumot o‘zgargan yoki allaqachon mavjud. Yangilang."}, status=409
        )
    except Exception:
        logger.exception("API failed: %s", route)
        return JsonResponse({"error": "Server xatosi. Keyinroq qayta urinib ko‘ring."}, status=500)


def dispatch(request, parts):
    route = "/".join(parts)
    if route == "session":
        method(request, "GET")
        token = get_token(request)
        try:
            user = session_user(request)
        except Problem:
            user = None
        return {
            "user": user_data(user) if user else None,
            "csrf": token,
            "email_delivery": "console" if "console" in settings.EMAIL_BACKEND else "smtp",
        }

    if parts[0] == "auth":
        method(request, "POST")
        data = body(request)
        if route == "auth/logout":
            if request.user.is_authenticated:
                ListeningAttempt.objects.filter(
                    user=request.user, session_key=request.session.session_key, status="active"
                ).update(status="cancelled")
            logout(request)
            return {"ok": True}
        if route in {"auth/login", "auth/register", "auth/reset"}:
            email = text(data, "email", 254).lower()
            validate_email(email)
            throttle(request, route, limit=30)
            throttle(request, route + "-email", email, limit=8)
        if route == "auth/register":
            user = User(email=email, name=text(data, "name", 120))
            password = text(data, "password", 128)
            try:
                validate_password(password, user)
            except ValidationError as error:
                raise Problem(" ".join(error.messages))
            user.set_password(password)
            user.save()
        elif route == "auth/login":
            user = authenticate(request, email=email, password=data.get("password", ""))
            if not user:
                raise Problem("Email yoki parol noto‘g‘ri, yoki hisob bloklangan.", 401)
        elif route == "auth/reset":
            user = User.objects.filter(email=email, is_active=True).first()
            if user:
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                link = f"{settings.PUBLIC_ORIGIN}/?reset={uid}&token={token}"
                send_mail(
                    "Listenify — parolni tiklash",
                    f"Parolni tiklash: {link}",
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                )
            return {"ok": True}
        elif route == "auth/reset-confirm":
            throttle(request, route)
            uid = urlsafe_base64_decode(text(data, "uid")).decode()
            user = User.objects.get(pk=uid, is_active=True)
            with transaction.atomic():
                user = User.objects.select_for_update().get(pk=user.pk)
                if not default_token_generator.check_token(user, text(data, "token")):
                    raise Problem("Tiklash havolasi eskirgan.")
                password = text(data, "password", 128)
                try:
                    validate_password(password, user)
                except ValidationError as error:
                    raise Problem(" ".join(error.messages))
                user.set_password(password)
                user.session_generation += 1
                user.save()
                invalidate_sessions(user)
            return {"ok": True}
        else:
            raise Problem("Manzil topilmadi.", 404)
        login(request, user)
        request.session["generation"] = user.session_generation
        AuthSession.objects.update_or_create(
            session_id=request.session.session_key, defaults={"user": user}
        )
        return {"user": user_data(user), "csrf": get_token(request)}

    user = session_user(request)
    if route == "materials":
        method(request, "GET")
        counts = ListeningResult.objects.filter(
            user=user, version_id=OuterRef("current_version_id")
        ).values("count")[:1]
        items = (
            Material.objects.select_related("current_version")
            .annotate(
                my_listen_count=Coalesce(Subquery(counts, output_field=IntegerField()), Value(0))
            )
            .order_by("-created_at")
        )
        if user.role != "admin":
            items = items.filter(status="published").exclude(
                current_version__level__in=blocked_levels(user)
            )
        query = request.GET.get("q", "").strip()
        if query:
            items = items.filter(title__icontains=query)
        if request.GET.get("level"):
            items = items.filter(current_version__level=request.GET["level"])
        return [material_data(item, user) for item in items]
    if parts[0] == "materials" and len(parts) == 2:
        method(request, "GET")
        item = Material.objects.select_related("current_version").get(pk=parts[1])
        if not item.current_version:
            raise Problem("Audio hali yuklanmagan.", 404)
        can_practice(user, item.current_version)
        return material_data(item, user, True)
    if parts[0] == "versions" and len(parts) == 3:
        version = MaterialVersion.objects.select_related("material").get(pk=parts[1])
        can_practice(user, version)
        if parts[2] == "media":
            method(request, "GET")
            return media.stream(request, version)
        if parts[2] == "attempts":
            method(request, "POST")
            attempt = listening.start(user, version, request.session.session_key)
            return {"id": str(attempt.pk)}
        if parts[2] == "script":
            method(request, "GET")
            return {"script": version.script}
    if parts[0] == "attempts" and len(parts) == 3:
        method(request, "POST")
        if parts[2] == "heartbeat":
            result = listening.heartbeat(user, parts[1], request.session.session_key, body(request))
            if isinstance(result, Problem):
                raise result
            return {"ok": True, "sequence": result.sequence}
        if parts[2] == "finish":
            return {"count": listening.finish(user, parts[1], request.session.session_key)}
        if parts[2] == "cancel":
            listening.cancel(user, parts[1], request.session.session_key)
            return {"ok": True}
    if route == "recordings":
        method(request, "GET", "POST")
        if request.method == "GET":
            records = (
                Recording.objects.filter(user=user)
                .select_related("user", "version__material", "review")
                .order_by("-created_at")
            )
            return [recording_data(r) for r in records]
        version = MaterialVersion.objects.select_related("material").get(
            pk=request.POST.get("version_id")
        )
        can_practice(user, version)
        upload_key = uuid.UUID(request.POST.get("upload_key", ""))
        uploaded = media.receive(request.FILES.get("audio"), recording=True)
        try:
            with transaction.atomic():
                user = lock_active_user(user)
                version.refresh_from_db()
                can_practice(user, version)
                existing = Recording.objects.filter(user=user, upload_key=upload_key).first()
                if existing:
                    if existing.digest != uploaded["digest"] or existing.version_id != version.pk:
                        raise Problem("Bu upload identifikatori boshqa faylga tegishli.", 409)
                    media.queue_cleanup(uploaded["file_key"])
                    transaction.on_commit(media.cleanup, robust=True)
                    return recording_data(existing)
                record = Recording.objects.create(
                    user=user, version=version, upload_key=upload_key, **uploaded
                )
            return recording_data(record)
        except Exception:
            media.queue_cleanup(uploaded["file_key"])
            transaction.on_commit(media.cleanup, robust=True)
            raise
    if parts[0] == "recordings" and len(parts) in {2, 3}:
        with transaction.atomic():
            record = (
                Recording.objects.select_for_update(of=("self",))
                .select_related("version__material", "user", "review")
                .get(pk=parts[1])
            )
            if record.user_id != user.pk and user.role != "admin":
                raise Problem("Yozuvga ruxsat yo‘q.", 403)
            if len(parts) == 3 and parts[2] == "media":
                method(request, "GET")
                return media.stream(request, record)
            if len(parts) == 3 and parts[2] == "submit":
                method(request, "POST")
                if record.user_id != user.pk:
                    raise Problem("Faqat egasi yuborishi mumkin.", 403)
                if record.status == "saved":
                    record.status, record.submitted_at = "submitted", timezone.now()
                    record.save()
                return recording_data(record)
            if len(parts) == 2:
                method(request, "DELETE")
                if record.user_id != user.pk or record.status != "saved":
                    raise Problem("Faqat o‘z yuborilmagan yozuvingizni o‘chira olasiz.", 403)
                media.queue_cleanup(record.file_key)
                record.delete()
                transaction.on_commit(media.cleanup, robust=True)
                return {"ok": True}
    if parts[0] == "admin":
        require_admin(user)
        return admin_dispatch(request, parts[1:], user)
    raise Problem("Manzil topilmadi.", 404)


def admin_dispatch(request, parts, user):
    route = "/".join(parts)
    if route == "overview":
        method(request, "GET")
        return {
            "students": User.objects.filter(role="student").count(),
            "groups": Classroom.objects.count(),
            "pending": Recording.objects.filter(status="submitted").count(),
        }
    if route == "users":
        method(request, "GET")
        result = []
        listen_counts = (
            ListeningResult.objects.filter(user_id=OuterRef("pk"))
            .order_by()
            .values("user_id")
            .annotate(total=Sum("count"))
            .values("total")
        )
        users = (
            User.objects.select_related("group")
            .prefetch_related("level_blocks", "group__level_blocks")
            .annotate(
                listens_total=Coalesce(
                    Subquery(listen_counts, output_field=IntegerField()), Value(0)
                ),
                recordings_total=Count("recordings", distinct=True),
            )
            .order_by("name")
        )
        for item in users:
            row = user_data(item)
            row["listens"] = item.listens_total
            row["recordings"] = item.recordings_total
            result.append(row)
        return result
    if route == "listening":
        method(request, "GET")
        results = ListeningResult.objects.select_related(
            "user__group", "version__material"
        ).order_by("user__name", "version__material__title")
        for query, field in [
            ("user_id", "user_id"),
            ("group_id", "user__group_id"),
            ("material_id", "version__material_id"),
        ]:
            if request.GET.get(query):
                results = results.filter(**{field: request.GET[query]})
        return [
            {
                "user_id": str(r.user_id),
                "user_name": r.user.name,
                "group_name": r.user.group.name if r.user.group_id else None,
                "material_id": str(r.version.material_id),
                "title": r.version.material.title,
                "number": r.version.number,
                "level": r.version.level,
                "count": r.count,
            }
            for r in results
        ]
    if parts[0] == "users" and len(parts) == 2:
        method(request, "PATCH", "DELETE")
        with transaction.atomic():
            target = User.objects.select_for_update().get(pk=parts[1])
            if target.pk == user.pk:
                raise Problem("Joriy admin o‘z hisobini bu yerdan bloklay/o‘chira olmaydi.")
            if request.method == "DELETE":
                if body(request).get("confirm_email") != target.email:
                    raise Problem("Tasdiqlash uchun hisob emailini kiriting.")
                for key in target.recordings.values_list("file_key", flat=True):
                    media.queue_cleanup(key)
                invalidate_sessions(target)
                target.delete()
                transaction.on_commit(media.cleanup, robust=True)
                return {"ok": True}
            active = body(request).get("active")
            if not isinstance(active, bool):
                raise Problem("active boolean bo‘lishi kerak.")
            target.is_active = active
            target.session_generation += 1
            target.save()
            invalidate_sessions(target)
            return user_data(target)
    if route == "groups":
        method(request, "GET", "POST")
        if request.method == "POST":
            Classroom.objects.create(name=text(body(request), "name", 120))
        groups = (
            Classroom.objects.annotate(student_count=Count("students"))
            .prefetch_related("level_blocks")
            .order_by("name")
        )
        return [
            {
                "id": g.pk,
                "name": g.name,
                "students": g.student_count,
                "blocked_levels": [block.level for block in g.level_blocks.all()],
            }
            for g in groups
        ]
    if parts[0] == "groups" and len(parts) == 2:
        method(request, "PATCH")
        group = Classroom.objects.get(pk=parts[1])
        group.name = text(body(request), "name", 120)
        group.save()
        return {"ok": True}
    if route == "transfer":
        method(request, "POST")
        data = body(request)
        ids = data.get("user_ids")
        if not isinstance(ids, list) or not ids or len(ids) > 500:
            raise Problem("1–500 o‘quvchini tanlang.")
        ids = {uuid.UUID(str(i)) for i in ids}
        with transaction.atomic():
            group = (
                Classroom.objects.get(pk=data["group_id"])
                if data.get("group_id") is not None
                else None
            )
            users = list(
                User.objects.select_for_update().filter(pk__in=ids, role="student").order_by("pk")
            )
            if len(users) != len(ids):
                raise Problem("Tanlangan o‘quvchilar topilmadi.")
            User.objects.filter(pk__in=ids).update(group=group)
        return {"ok": True}
    if route == "restrictions":
        method(request, "POST")
        data = body(request)
        if data.get("level") not in dict(LEVELS) or not isinstance(data.get("blocked"), bool):
            raise Problem("Daraja yoki holat noto‘g‘ri.")
        if data.get("kind") not in {"user", "group"}:
            raise Problem("Cheklov turi noto‘g‘ri.")
        cls, owner = (
            (PersonalLevelBlock, "user") if data["kind"] == "user" else (GroupLevelBlock, "group")
        )
        with transaction.atomic():
            target = (
                (User if owner == "user" else Classroom)
                .objects.select_for_update()
                .get(pk=data["id"])
            )
            fields = {owner: target, "level": data["level"]}
            if data["blocked"]:
                cls.objects.get_or_create(**fields)
            else:
                cls.objects.filter(**fields).delete()
        return {"ok": True}
    if route == "materials":
        method(request, "POST")
        return save_material(request, user)
    if parts[0] == "materials" and len(parts) == 2:
        method(request, "POST", "PATCH")
        return save_material(request, user, parts[1])
    if route == "recordings":
        method(request, "GET")
        records = Recording.objects.select_related("user", "version__material", "review").order_by(
            "-created_at"
        )
        for query, field in [
            ("user_id", "user_id"),
            ("group_id", "user__group_id"),
            ("material_id", "version__material_id"),
            ("status", "status"),
        ]:
            if request.GET.get(query):
                records = records.filter(**{field: request.GET[query]})
        return [recording_data(record) for record in records]
    if parts[0] == "recordings" and len(parts) == 3:
        record = Recording.objects.select_related("version__material").get(pk=parts[1])
        if parts[2] == "source":
            method(request, "GET")
            return {
                "script": record.version.script,
                "audio_url": f"/api/versions/{record.version_id}/media",
            }
        if parts[2] == "review":
            method(request, "POST", "PATCH")
            data = body(request)
            score = data.get("score")
            if type(score) is not int or score not in range(1, 6):
                raise Problem("Baho 1–5 butun son bo‘lishi kerak.")
            comment = text(data, "comment", 5000)
            with transaction.atomic():
                record = Recording.objects.select_for_update().get(pk=record.pk)
                review = Review.objects.filter(recording=record).first()
                revision = review.revision if review else 0
                if (
                    data.get("revision") != revision
                    or (request.method == "POST" and review)
                    or (request.method == "PATCH" and not review)
                ):
                    raise Problem("Baho o‘zgargan. Sahifani yangilang.", 409)
                if record.status not in {"submitted", "graded"}:
                    raise Problem("Yozuv tekshirishga yuborilmagan.", 409)
                if not review:
                    review = Review(recording=record, reviewer=user, reviewer_name=user.name)
                else:
                    review.revision += 1
                review.score, review.comment = score, comment
                review.editor, review.editor_name = user, user.name
                review.save()
                record.status = "graded"
                record.save()
            return recording_data(
                Recording.objects.select_related("user", "version__material", "review").get(
                    pk=record.pk
                )
            )
    raise Problem("Manzil topilmadi.", 404)


def save_material(request, user, material_id=None):
    data = body(request)
    uploaded = media.receive(request.FILES.get("audio")) if request.FILES.get("audio") else None
    try:
        with transaction.atomic():
            item = (
                Material.objects.select_for_update().get(pk=material_id)
                if material_id
                else Material()
            )
            item.title = text(data, "title", 180)
            item.description = str(data.get("description", ""))[:5000]
            status = data.get("status", "draft")
            if status not in {"draft", "published", "archived"}:
                raise Problem("Material holati noto‘g‘ri.")
            item.status = status
            script = text(data, "script", 50000)
            level = data.get("level")
            if level not in dict(LEVELS):
                raise Problem("Darajani tanlang.")
            previous = item.current_version if item.pk and item.current_version_id else None
            if not previous and not uploaded:
                raise Problem("Audio fayl majburiy.")
            item.save()
            if uploaded or not previous or previous.script != script or previous.level != level:
                values = (
                    {k: v for k, v in uploaded.items() if k != "digest"}
                    if uploaded
                    else {
                        "file_key": previous.file_key,
                        "mime": previous.mime,
                        "duration": previous.duration,
                    }
                )
                version = MaterialVersion.objects.create(
                    material=item,
                    number=(previous.number + 1 if previous else 1),
                    script=script,
                    level=level,
                    **values,
                )
                item.current_version = version
                item.save()
        return material_data(item, user, True)
    except Exception:
        if uploaded:
            media.queue_cleanup(uploaded["file_key"])
            transaction.on_commit(media.cleanup, robust=True)
        raise


def frontend(request):
    root = (settings.BASE_DIR / "frontend" / "dist").resolve()
    candidate = (root / request.path.lstrip("/")).resolve()
    if candidate.is_relative_to(root) and candidate.is_file():
        return FileResponse(candidate.open("rb"))
    index = root / "index.html"
    if index.is_file():
        return FileResponse(index.open("rb"), content_type="text/html")
    return HttpResponse(
        "Frontend uchun: cd frontend; npm run dev. Yoki npm run build.", content_type="text/plain"
    )
