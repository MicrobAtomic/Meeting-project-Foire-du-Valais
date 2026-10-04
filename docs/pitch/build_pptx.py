"""Build a static PPTX with one image per slide, manual advancement and French notes.
Run via uv --no-project --with python-pptx python build_pptx.py in docs/pitch.
"""
import json
from pathlib import Path
from pptx import Presentation
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Emu
HERE=Path(__file__).resolve().parent
WIDTH,HEIGHT=Emu(12192000),Emu(6858000)
slides=json.loads((HERE/'slides/slides.json').read_text())
deck=Presentation()
deck.slide_width,deck.slide_height=WIDTH,HEIGHT
for info in slides:
    slide=deck.slides.add_slide(deck.slide_layouts[6])
    slide.shapes.add_picture(str(HERE/info['image']),0,0,WIDTH,HEIGHT)
    transition=OxmlElement('p:transition')
    transition.set('advClick','1')
    slide._element.insert_element_before(transition,'p:timing','p:extLst')
    slide.notes_slide.notes_text_frame.text=info['notes']
# Atomic replacement also avoids leaving a partial file if export fails.
output=HERE/'Club-des-Affaires-pitch.pptx'
temporary=HERE/'.build/pitch-export.pptx'
temporary.parent.mkdir(exist_ok=True)
deck.save(temporary)
temporary.replace(output)
print(f'{output.name}: {len(slides)} static slides and French notes')
