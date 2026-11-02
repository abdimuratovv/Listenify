"""Reject oversized media before Django stores it in a temporary file."""

import re

from django.core.files.uploadhandler import FileUploadHandler, StopUpload
from django.http import JsonResponse

MIB = 1024 * 1024
FORM_OVERHEAD = MIB


def upload_limit(path):
    """Return the total file-data limit for supported multipart endpoints."""
    path = path.rstrip("/")
    if path == "/api/recordings":
        return 50 * MIB
    if re.fullmatch(r"/api/admin/materials(?:/[0-9a-fA-F-]+)?", path):
        return 100 * MIB
    return None


def too_large():
    return JsonResponse(
        {"error": "Yuklanayotgan fayl hajmi ruxsat etilgan chegaradan oshdi."}, status=413
    )


class MediaUploadLimitHandler(FileUploadHandler):
    """Count all file chunks before forwarding them to Django's normal handlers."""

    def __init__(self, request=None):
        super().__init__(request)
        self.limit = upload_limit(request.path_info) if request else None
        self.total = 0

    def receive_data_chunk(self, raw_data, start):
        if self.limit is not None:
            self.total += len(raw_data)
            if self.total > self.limit:
                self.request.media_upload_too_large = True
                raise StopUpload(connection_reset=True)
        return raw_data

    def file_complete(self, file_size):
        return None


class MediaUploadLimitMiddleware:
    """Check declared size and parse multipart before passing a rejected upload on."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        limit = upload_limit(request.path_info)
        if (
            limit is not None
            and request.method == "POST"
            and request.content_type == "multipart/form-data"
        ):
            try:
                declared = int(request.META.get("CONTENT_LENGTH") or 0)
            except ValueError:
                declared = 0
            if declared > limit + FORM_OVERHEAD:
                return too_large()
            # Triggers the handler before any mutation in the view. A proxy limit
            # is still recommended to reject oversized requests at the edge.
            request.POST
            if getattr(request, "media_upload_too_large", False):
                return too_large()
        return self.get_response(request)
