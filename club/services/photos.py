"""Decode untrusted images and store only private, normalised JPEG portraits."""
import logging
import uuid
import warnings
from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils.translation import gettext as _
from PIL import Image, ImageOps, UnidentifiedImageError

from club.models import Member

logger = logging.getLogger(__name__)
MAX_BYTES = 2 * 1024 * 1024


def normalize_member_photo(upload):
    message = _("Photo invalide : JPEG, PNG ou WebP non animé, 2 Mio et 4096 × 4096 pixels maximum.")
    if upload.size > MAX_BYTES:
        raise ValidationError(message)
    upload.seek(0)
    raw = upload.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValidationError(message)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw), formats=["JPEG", "PNG", "WEBP"]) as image:
                width, height = image.size
                if max(width, height) > 4096 or width * height > 16_000_000 or getattr(image, "n_frames", 1) != 1:
                    raise ValidationError(message)
                image.verify()
            with Image.open(BytesIO(raw), formats=["JPEG", "PNG", "WEBP"]) as image:
                image.load()
                oriented = ImageOps.exif_transpose(image).convert("RGBA")
                cropped = ImageOps.fit(oriented, (512, 512), method=Image.Resampling.LANCZOS)
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
                member.photo = new_name
            elif remove:
                member.photo = ""
            member.save()
            if (normalized is not None or remove) and old_name:
                transaction.on_commit(lambda: delete_unreferenced_photo(old_name, storage))
    except Exception:
        if new_name:
            storage.delete(new_name)
        member.photo = old_name
        raise
    return member


def available_photo(member):
    if member.photo and member.photo.storage.exists(member.photo.name):
        return True
    if member.photo:
        logger.warning("Missing private portrait for member id=%s", member.pk)
    return False
