from django.core.exceptions import ValidationError

from club.models import PersonalNote
from club.services.access import visible_target


def get_personal_note(owner, target):
    return PersonalNote.objects.filter(owner=owner, target=target).first()


def save_personal_note(owner, target, text):
    visible_target(owner, target.pk)
    if owner.pk == target.pk:
        raise ValidationError("self")
    text = text.strip()
    if len(text) > 2000:
        raise ValidationError("length")
    if not text:
        PersonalNote.objects.filter(owner=owner, target=target).delete()
        return None
    note, _ = PersonalNote.objects.update_or_create(owner=owner, target=target, defaults={"text": text})
    return note
