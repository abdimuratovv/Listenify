import hashlib
import json
import re
import subprocess
import uuid
from pathlib import Path
from datetime import timedelta
from django.conf import settings
from django.http import FileResponse, StreamingHttpResponse, HttpResponse
from django.utils import timezone
from .models import FileCleanupJob, MaterialVersion, Recording
from .policy import Problem


def private_path(key):
    root = Path(settings.PRIVATE_ROOT).resolve()
    path = (root / key).resolve()
    if path.parent != root:
        raise Problem("Noto‘g‘ri fayl manzili.")
    return path


def receive(upload, recording=False):
    limit = (50 if recording else 100) * 1024 * 1024
    if not upload or upload.size <= 0 or upload.size > limit:
        raise Problem(f"Audio hajmi 1 baytdan {limit // 1024 // 1024} MiB gacha bo‘lsin.")
    key = uuid.uuid4().hex + ".media"
    path = private_path(key)
    digest = hashlib.sha256()
    try:
        total = 0
        with path.open("wb") as stream:
            for chunk in upload.chunks():
                total += len(chunk)
                if total > limit:
                    raise Problem("Fayl hajmi chegaradan oshdi.")
                digest.update(chunk)
                stream.write(chunk)
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
            capture_output=True,
            timeout=20,
            check=True,
        )
        info = json.loads(result.stdout)
        streams = info.get("streams", [])
        if not any(s.get("codec_type") == "audio" for s in streams) or any(
            s.get("codec_type") == "video" for s in streams
        ):
            raise Problem("Faqat audio fayl yuklang; video qabul qilinmaydi.")
        raw_duration = info["format"].get("duration")
        if raw_duration is None:
            # Browser MediaRecorder WebM frequently has no container duration.
            packets = (
                subprocess.run(
                    [
                        "ffprobe",
                        "-v",
                        "error",
                        "-select_streams",
                        "a:0",
                        "-show_entries",
                        "packet=pts_time,duration_time",
                        "-of",
                        "csv=p=0",
                        str(path),
                    ],
                    capture_output=True,
                    timeout=20,
                    check=True,
                )
                .stdout.decode()
                .splitlines()
            )
            ends = []
            for row in packets:
                fields = row.split(",")
                try:
                    ends.append(
                        float(fields[0])
                        + (float(fields[1]) if len(fields) > 1 and fields[1] != "N/A" else 0)
                    )
                except ValueError:
                    continue
            raw_duration = max(ends, default=0)
        duration = float(raw_duration)
        if not 0 < duration <= (600 if recording else 1800):
            raise Problem("Audio davomiyligi ruxsat etilgan chegarada emas.")
        formats = info["format"]["format_name"].split(",")
        types = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "ogg": "audio/ogg",
            "webm": "audio/webm",
            "matroska": "audio/webm",
            "mov": "audio/mp4",
            "mp4": "audio/mp4",
            "flac": "audio/flac",
        }
        mime = next((types[f] for f in formats if f in types), None)
        if not mime:
            raise Problem("Bu audio formati qo‘llanmaydi.")
        return {"file_key": key, "mime": mime, "duration": duration, "digest": digest.hexdigest()}
    except (subprocess.SubprocessError, ValueError, KeyError, OSError) as error:
        path.unlink(missing_ok=True)
        raise Problem(
            "Audio tekshirilmadi. Fayl va serverdagi ffprobe sozlamasini tekshiring."
        ) from error
    except Exception:
        path.unlink(missing_ok=True)
        raise


def queue_cleanup(key):
    FileCleanupJob.objects.get_or_create(file_key=key)


def cleanup():
    for job in FileCleanupJob.objects.filter(next_attempt_at__lte=timezone.now()):
        try:
            # Never erase media still referenced by a committed model.
            if (
                MaterialVersion.objects.filter(file_key=job.file_key).exists()
                or Recording.objects.filter(file_key=job.file_key).exists()
            ):
                job.delete()
                continue
            private_path(job.file_key).unlink(missing_ok=True)
            job.delete()
        except OSError as error:
            job.attempts += 1
            job.error = str(error)
            job.next_attempt_at = timezone.now() + timedelta(
                minutes=min(1440, 2 ** min(job.attempts, 10))
            )
            job.save()
    # Interrupted uploads never reached a DB row or a cleanup job.
    cutoff = timezone.now().timestamp() - 86400
    referenced = set(MaterialVersion.objects.values_list("file_key", flat=True)) | set(
        Recording.objects.values_list("file_key", flat=True)
    )
    for path in Path(settings.PRIVATE_ROOT).glob("*.media"):
        if path.name not in referenced and path.stat().st_mtime < cutoff:
            try:
                path.unlink()
            except OSError:
                queue_cleanup(path.name)


def stream(request, item):
    path = private_path(item.file_key)
    if not path.is_file():
        raise Problem("Audio fayli topilmadi.", 404)
    size = path.stat().st_size
    value = request.headers.get("Range")
    if value:
        match = re.fullmatch(r"bytes=(\d*)-(\d*)", value)
        if not match or not any(match.groups()):
            return HttpResponse(status=416, headers={"Content-Range": f"bytes */{size}"})
        begin, end = match.groups()
        if not begin:
            begin, end = max(0, size - int(end)), size - 1
        else:
            begin, end = int(begin), min(int(end) if end else size - 1, size - 1)
        if begin >= size or begin > end:
            return HttpResponse(status=416, headers={"Content-Range": f"bytes */{size}"})

        def chunks():
            with path.open("rb") as source:
                source.seek(begin)
                remaining = end - begin + 1
                while remaining:
                    block = source.read(min(65536, remaining))
                    if not block:
                        break
                    remaining -= len(block)
                    yield block

        response = StreamingHttpResponse(chunks(), status=206, content_type=item.mime)
        response["Content-Range"] = f"bytes {begin}-{end}/{size}"
        response["Content-Length"] = end - begin + 1
    else:
        response = FileResponse(path.open("rb"), content_type=item.mime)
    response["Cache-Control"] = "private, no-store"
    response["Accept-Ranges"] = "bytes"
    response["X-Content-Type-Options"] = "nosniff"
    return response
