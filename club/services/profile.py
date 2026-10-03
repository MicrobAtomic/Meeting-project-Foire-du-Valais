from club.models import MemberTag, Tag


def save_tag_answers(member, data) -> int:
    """Store 'tag_<slug>' = like|neutral|dislike answers for THIS member. Unknown values are ignored."""
    valid = set(MemberTag.Sentiment.values)
    saved = 0
    for tag in Tag.objects.all():
        value = data.get(f"tag_{tag.slug}")
        if value in valid:
            MemberTag.objects.update_or_create(member=member, tag=tag, defaults={"sentiment": value})
            saved += 1
    return saved


def common_tags(me, other) -> dict:
    """{'likes': [Tag], 'dislikes': [Tag]} shared by two members ('Vos points communs')."""
    result = {}
    for sentiment, key in ((MemberTag.Sentiment.LIKE, "likes"), (MemberTag.Sentiment.DISLIKE, "dislikes")):
        mine = MemberTag.objects.filter(member=me, sentiment=sentiment).values("tag_id")
        result[key] = list(
            Tag.objects.filter(member_links__member=other, member_links__sentiment=sentiment, id__in=mine)
        )
    return result
