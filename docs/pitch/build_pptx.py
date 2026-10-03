"""Builds Club-des-Affaires-pitch.pptx from the slide images (build_deck.mjs): one full-bleed image per slide, the
demo video embedded on its slide, and the French talk in the speaker notes. Usage, from docs/pitch/:
    uv run --no-project --with python-pptx python build_pptx.py
"""

import json
from pathlib import Path

from pptx import Presentation
from pptx.util import Emu

HERE = Path(__file__).parent
WIDTH, HEIGHT = Emu(12192000), Emu(6858000)  # 16:9, 13.333 x 7.5 in
PX = WIDTH / 1920  # the slides are designed at 1920 x 1080 px

slides = json.loads((HERE / "slides" / "slides.json").read_text())
deck = Presentation()
deck.slide_width, deck.slide_height = WIDTH, HEIGHT
blank = deck.slide_layouts[6]

for info in slides:
    slide = deck.slides.add_slide(blank)
    slide.shapes.add_picture(str(HERE / info["image"]), 0, 0, WIDTH, HEIGHT)
    if info["video"]:
        box = info["video"]
        slide.shapes.add_movie(
            str(HERE / "demo.mp4"),
            Emu(int(box["x"] * PX)), Emu(int(box["y"] * PX)), Emu(int(box["w"] * PX)), Emu(int(box["h"] * PX)),
            poster_frame_image=str(HERE / "demo-poster.png"),
            mime_type="video/mp4",
        )
    slide.notes_slide.notes_text_frame.text = info["notes"]

output = HERE / "Club-des-Affaires-pitch.pptx"
deck.save(output)
print(f"{output.name}: {len(slides)} slides")
