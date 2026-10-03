"""Decode untrusted images and store only private, normalised JPEG portraits."""
import logging
import uuid
import warnings
from contextlib import contextmanager
from contextvars import ContextVar
from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils.translation import gettext as _
from PIL import Image, ImageOps, UnidentifiedImageError
from pillow_heif import register_heif_opener

from club.models import Member

logger = logging.getLogger(__name__)
MAX_BYTES = 20 * 1024 * 1024
MAX_EDGE = 10_000
MAX_PIXELS = 50_000_000
PHOTO_FORMATS = ("JPEG", "PNG", "WEBP", "HEIF", "AVIF")
register_heif_opener(thumbnails=False, depth_images=False, aux_images=False, decode_threads=1)
_photo_writes = ContextVar("club_photo_writes", default=None)


@contextmanager
def photo_write_scope():
    """Wrap the outer database transaction to clean new files after any rollback."""
    writes = []
    token = _photo_writes.set(writes)
    try:
        yield
    finally:
        _photo_writes.reset(token)
        for name, storage in writes:
            try:
                delete_unreferenced_photo(name, storage)
            except Exception:
                logger.exception("Could not clean an unreferenced portrait")


def normalize_member_photo(upload):
    message = _("Photo invalide : JPEG, PNG, WebP, HEIC/HEIF ou AVIF non animé, 20 Mio, 50 mégapixels et 10 000 pixels par côté maximum.")
    if upload.size > MAX_BYTES:
        raise ValidationError(message)
    upload.seek(0)
    raw = upload.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValidationError(message)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw), formats=PHOTO_FORMATS) as image:
                width, height = image.size
                if max(width, height) > MAX_EDGE or width * height > MAX_PIXELS or getattr(image, "n_frames", 1) != 1:
                    raise ValidationError(message)
                image.verify()
            with Image.open(BytesIO(raw), formats=PHOTO_FORMATS) as image:
                # JPEG can decode at a reduced resolution before loading a large phone picture.
                image.draft(None, (1024, 1024))
                image.load()
                cropped = ImageOps.fit(image, (512, 512), method=Image.Resampling.LANCZOS)
                # A centred square crop commutes with the EXIF transform; rotate only the small result.
                cropped = ImageOps.exif_transpose(cropped).convert("RGBA")
                clean = Image.new("RGB", (512, 512), "white")
                clean.paste(cropped, mask=cropped.getchannel("A"))
                result = BytesIO()
                clean.save(result, format="JPEG", quality=85, optimize=True)
        return ContentFile(result.getvalue(), name=f"{uuid.uuid4().hex}.jpg")
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError, Image.DecompressionBombWarning, Image.DecompressionBombError):
        raise ValidationError(message) from None


def delete_unreferenced_photo(name, storage):
    if name and not Member.objects.filter(photo=name).exists():
        storage.delete(name)


def save_profile_photo(member, normalized=None, remove=False, old_name=None):
    """Save the complete validated profile, cleaning new files on failure and old files on commit."""
    storage = Member._meta.get_field("photo").storage
    old_name = old_name if old_name is not None else (member.photo.name or "")
    new_name = ""
    try:
        with transaction.atomic():
            if normalized is not None:
                new_name = storage.save(f"member_photos/{uuid.uuid4().hex}.jpg", normalized)
                writes = _photo_writes.get()
                if writes is not None:
                    writes.append((new_name, storage))
                member.photo = new_name
            elif remove:
                member.photo = ""
            member.save()
            if (normalized is not None or remove) and old_name:
                transaction.on_commit(lambda: delete_unreferenced_photo(old_name, storage), robust=True)
    except Exception:
        if new_name:
            delete_unreferenced_photo(new_name, storage)
        member.photo = old_name
        raise
    return member


def available_photo(member):
    if member.photo and member.photo.storage.exists(member.photo.name):
        return True
    if member.photo:
        logger.warning("Missing private portrait for member id=%s", member.pk)
    return False
