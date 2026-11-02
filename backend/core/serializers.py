from .models import ListeningResult
from .policy import blocked_levels


def user_data(user):
    personal = [block.level for block in user.level_blocks.all()]
    return {
        "id": str(user.pk),
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "active": user.is_active,
        "group_id": user.group_id,
        "group_name": user.group.name if user.group_id else None,
        "blocked_levels": sorted(blocked_levels(user, personal)),
        "personal_blocks": personal,
    }


def material_data(material, user, detail=False):
    version = material.current_version
    result = {
        "id": str(material.pk),
        "title": material.title,
        "description": material.description,
        "status": material.status,
    }
    if version:
        result.update(
            version_id=str(version.pk),
            number=version.number,
            level=version.level,
            duration=version.duration,
        )
        count = getattr(material, "my_listen_count", None)
        if count is None:
            count = (
                ListeningResult.objects.filter(user=user, version=version)
                .values_list("count", flat=True)
                .first()
                or 0
            )
        result["count"] = count
        if detail:
            result["script"] = version.script
            result["audio_url"] = f"/api/versions/{version.pk}/media"
    return result


def recording_data(record):
    review = getattr(record, "review", None)
    return {
        "id": str(record.pk),
        "user_id": str(record.user_id),
        "user_name": record.user.name,
        "group_id": record.user.group_id,
        "material_id": str(record.version.material_id),
        "title": record.version.material.title,
        "version_id": str(record.version_id),
        "number": record.version.number,
        "duration": record.duration,
        "status": record.status,
        "created_at": record.created_at.isoformat(),
        "audio_url": f"/api/recordings/{record.pk}/media",
        "review": {
            "score": review.score,
            "comment": review.comment,
            "reviewer": review.reviewer_name,
            "reviewed_at": review.reviewed_at.isoformat(),
            "editor": review.editor_name,
            "edited_at": review.edited_at.isoformat(),
            "revision": review.revision,
        }
        if review
        else None,
    }
