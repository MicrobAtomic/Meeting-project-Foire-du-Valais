"""Build a portable PPTX: static slide backgrounds, original animated GIFs and French notes.
Run via uv --no-project --with python-pptx python build_pptx.py in docs/pitch.
"""
import json
from pathlib import Path
from pptx import Presentation
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Emu
HERE = Path(__file__).resolve().parent
WIDTH, HEIGHT = Emu(12192000), Emu(6858000)
PX = WIDTH / 1920
slides = json.loads((HERE/'slides/slides.json').read_text())
deck = Presentation()
deck.slide_width, deck.slide_height = WIDTH, HEIGHT
for info in slides:
    slide = deck.slides.add_slide(deck.slide_layouts[6])
    slide.shapes.add_picture(str(HERE/info['image']),0,0,WIDTH,HEIGHT)
    for animation in info['animations']:
        picture = slide.shapes.add_picture(str(HERE/animation['source']),
            *[Emu(round(animation[key]*PX)) for key in ('x','y','w','h')])
        if animation['radius']:
            geometry = picture._element.spPr.prstGeom
            geometry.set('prst','roundRect')
            adjustment = OxmlElement('a:gd')
            adjustment.set('name','adj')
            adjustment.set('fmla',f"val {round(100000*animation['radius']/min(animation['w'],animation['h']))}")
            geometry.avLst.append(adjustment)
        picture.name = f"Animated demo: {animation['source']}"
    # Explicit manual advancement; no timed transition or full-length movie.
    transition = OxmlElement('p:transition')
    transition.set('advClick','1')
    slide._element.insert_element_before(transition,'p:timing','p:extLst')
    slide.notes_slide.notes_text_frame.text = info['notes']
output=HERE/'Club-des-Affaires-pitch.pptx'
deck.save(output)
print(f'{output.name}: {len(slides)} slides with embedded GIFs')
