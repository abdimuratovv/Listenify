from .models import User


class Problem(Exception):
    def __init__(self, message, status=400):
        self.message, self.status = message, status


def require_admin(user):
    if user.role != "admin":
        raise Problem("Admin huquqi kerak.", 403)


def lock_active_user(user):
    """Recheck account state and membership after acquiring its transaction lock."""
    current = User.objects.select_for_update().get(pk=user.pk)
    if not current.is_active or current.session_generation != user.session_generation:
        raise Problem("Sessiya tugatilgan. Qayta kiring.", 401)
    return current


def blocked_levels(user, personal=None):
    if personal is None:
        personal = {block.level for block in user.level_blocks.all()}
    else:
        personal = set(personal)
    group = {block.level for block in user.group.level_blocks.all()} if user.group_id else set()
    return personal | group


def can_practice(user, version):
    if user.role == "admin":
        return
    if version.material.status != "published" or version.material.current_version_id != version.id:
        raise Problem("Bu audio arxivlangan yoki yangi versiyasi mavjud.", 403)
    if version.level in blocked_levels(user):
        raise Problem("Bu daraja siz uchun yopilgan.", 403)
