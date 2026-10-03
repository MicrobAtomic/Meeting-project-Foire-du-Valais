from django.conf import settings


def _escape(value: str) -> str:
    """RFC 6350 escaping: blocks vCard injection through newlines, ';' or ','."""
    value = value.replace("\\", "\\\\").replace("\r\n", "\n").replace("\r", "\n")
    return value.replace("\n", "\\n").replace(";", "\\;").replace(",", "\\,")


def build_vcard(member) -> str:
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"N:{_escape(member.last_name)};{_escape(member.first_name)};;;",
        f"FN:{_escape(member.full_name)}",
        f"ORG:{_escape(member.company)}",
        f"TITLE:{_escape(member.job_title)}",
    ]
    if member.user.email:
        lines.append(f"EMAIL;TYPE=INTERNET:{_escape(member.user.email)}")
    if member.phone:
        lines.append(f"TEL;TYPE=CELL:{_escape(member.phone)}")
    if member.linkedin_url:
        lines.append(f"URL:{_escape(member.linkedin_url)}")
    lines.append(f"NOTE:{_escape(settings.SITE_NAME + ' – Foire du Valais')}")
    lines.append("END:VCARD")
    return "\r\n".join(lines) + "\r\n"
