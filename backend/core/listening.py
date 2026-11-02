import math
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from .models import ListeningAttempt, ListeningResult, MaterialVersion
from .policy import Problem, can_practice, lock_active_user


def merged(intervals):
    result = []
    for start, end in sorted(intervals):
        if result and start <= result[-1][1]:
            result[-1][1] = max(end, result[-1][1])
        else:
            result.append([start, end])
    return result


@transaction.atomic
def start(user, version, session_key, now=None):
    # All starts and finishes for this user serialize on the same parent row.
    user = lock_active_user(user)
    version = MaterialVersion.objects.select_related("material").get(pk=version.pk)
    can_practice(user, version)
    ListeningAttempt.objects.filter(user=user, version=version, status="active").update(
        status="cancelled"
    )
    return ListeningAttempt.objects.create(
        user=user, version=version, session_key=session_key, last_at=now or timezone.now()
    )


def advance(attempt, payload, now):
    seq = payload.get("sequence")
    if not isinstance(seq, int) or isinstance(seq, bool) or seq != attempt.sequence + 1:
        raise Problem("Ijro hodisalari tartibi buzildi; boshidan boshlang.", 409)
    try:
        position = float(payload.get("position"))
    except (ValueError, TypeError):
        raise Problem("Ijro vaqti noto‘g‘ri.")
    duration = attempt.version.duration
    if not math.isfinite(position) or position < 0 or position > duration + 0.05:
        raise Problem("Ijro vaqti chegaradan tashqarida.")
    event = payload.get("event")
    if event not in {"play", "pause", "tick", "seek", "waiting", "ended"}:
        raise Problem("Noma’lum ijro hodisasi.")
    elapsed = max(0, (now - attempt.last_at).total_seconds())
    if elapsed > 5 and attempt.playing:
        raise Problem("Tarmoq tekshiruvi uzildi. Hisob uchun boshidan boshlang.", 409)
    delta = position - attempt.position
    if attempt.playing and event != "seek":
        if delta < -0.01:
            raise Problem("Vaqt sakrashi aniqlandi.", 409)
        if (
            delta > elapsed + 0.25
            or attempt.media_time + max(0, delta) > attempt.wall_time + elapsed + 0.25
        ):
            raise Problem("Oddiy ijro tezligi tasdiqlanmadi.", 409)
        if delta > 0:
            attempt.intervals = merged(
                attempt.intervals + [[attempt.position, min(position, duration)]]
            )
            attempt.media_time += delta
        attempt.wall_time += elapsed
    elif event not in {"seek"} and abs(delta) > 0.25:
        raise Problem("Ijro boshlanishi tasdiqlanmadi.", 409)
    attempt.position = min(position, duration)
    attempt.playing = event in {"play", "tick"}
    attempt.ended = event == "ended" and abs(duration - position) <= 0.25
    attempt.sequence = seq
    attempt.last_at = now


@transaction.atomic
def heartbeat(user, attempt_id, session_key, payload, now=None):
    user = lock_active_user(user)
    attempt = (
        ListeningAttempt.objects.select_for_update()
        .select_related("version__material")
        .get(pk=attempt_id, user=user)
    )
    if attempt.status != "active" or attempt.session_key != session_key:
        raise Problem("Urinish faol emas. Boshidan boshlang.", 409)
    can_practice(user, attempt.version)
    now = now or timezone.now()
    if now - attempt.last_at > timedelta(hours=24):
        attempt.status = "cancelled"
        attempt.save(update_fields=["status"])
        return Problem("Urinish muddati tugadi. Boshidan boshlang.", 409)
    try:
        advance(attempt, payload, now)
    except Problem as error:
        attempt.status = "cancelled"
        attempt.save(update_fields=["status"])
        # Return the error so cancellation survives the surrounding transaction.
        return error
    attempt.save()
    return attempt


def cancel(user, attempt_id, session_key):
    """Cancel only this user's active attempt in the session that created it."""
    ListeningAttempt.objects.filter(
        pk=attempt_id, user=user, session_key=session_key, status="active"
    ).update(status="cancelled")


@transaction.atomic
def finish(user, attempt_id, session_key):
    user = lock_active_user(user)
    attempt = (
        ListeningAttempt.objects.select_for_update()
        .select_related("version__material")
        .get(pk=attempt_id, user=user)
    )
    if attempt.session_key != session_key:
        raise Problem("Sessiya mos kelmadi.", 403)
    can_practice(user, attempt.version)
    if attempt.status == "completed":
        return ListeningResult.objects.get(user=user, version=attempt.version).count
    if attempt.status != "active" or (timezone.now() - attempt.last_at).total_seconds() > 5:
        raise Problem("Urinish faol emas.", 409)
    coverage = sum(end - begin for begin, end in merged(attempt.intervals))
    duration = attempt.version.duration
    if (
        not attempt.ended
        or coverage < duration - 0.25
        or min(attempt.wall_time, attempt.media_time) < duration - 0.25
    ):
        raise Problem("Audio to‘liq tinglanmagan. O‘tkazilgan qismlarni ham tinglang.", 409)
    result, _ = ListeningResult.objects.get_or_create(user=user, version=attempt.version)
    result.count += 1
    result.save(update_fields=["count"])
    attempt.status = "completed"
    attempt.save(update_fields=["status"])
    return result.count
