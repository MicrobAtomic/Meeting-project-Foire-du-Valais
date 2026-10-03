import segno


def qr_svg(url: str) -> str:
    """Inline SVG (no <img>, no external service, CSP-friendly)."""
    return segno.make(url, error="m").svg_inline(scale=6, border=2, dark="#1c1917", light="#ffffff")
