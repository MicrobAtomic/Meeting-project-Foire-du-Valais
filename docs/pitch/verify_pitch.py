"""Validate generated files without changing the app. Run via uv --with python-pptx."""
import hashlib
import json
from pathlib import Path
import re
from zipfile import ZipFile
from PIL import Image
from pptx import Presentation
HERE=Path(__file__).resolve().parent
slides=json.loads((HERE/'slides/slides.json').read_text())
story=json.loads((HERE/'story.json').read_text())
gifs=json.loads((HERE/'gifs/manifest.json').read_text())
deck=Presentation(HERE/'Club-des-Affaires-pitch.pptx')
assert len(slides)==len(deck.slides)==15
assert sum(s['seconds'] or 0 for s in slides)==118
assert len(story)==7 and len(gifs)==4
assert len(re.findall(rb'/Type\s*/Page\b',(HERE/'Club-des-Affaires-pitch.pdf').read_bytes()))==15
for row,slide in zip(slides,deck.slides):
    assert Image.open(HERE/row['image']).size==(1920,1080)
    assert slide.notes_slide.notes_text_frame.text==row['notes']
    assert len(slide.shapes)==1+len(row['animations'])
    if row['id']:
        script=next(s for s in story if s['id']==row['id'])
        assert row['notes'].endswith(script['text']) and row['seconds']==script['seconds']
        assert script['text'] in (HERE.parent/'PITCH.md').read_text()
    transition=slide._element.find('{http://schemas.openxmlformats.org/presentationml/2006/main}transition')
    assert transition is not None and transition.get('advClick')=='1' and transition.get('advTm') is None
    for shape,animation in zip(list(slide.shapes)[1:],row['animations']):
        assert shape.image.blob==(HERE/animation['source']).read_bytes()
with ZipFile(HERE/'Club-des-Affaires-pitch.pptx') as archive:
    embedded=[name for name in archive.namelist() if name.endswith('.gif')]
    assert len(embedded)==4
    assert not any(name.endswith('.mp4') for name in archive.namelist())
    embedded_hashes={hashlib.sha256(archive.read(name)).hexdigest() for name in embedded}
    assert embedded_hashes=={hashlib.sha256((HERE/value['gif']).read_bytes()).hexdigest() for value in gifs.values()}
for name,value in gifs.items():
    image=Image.open(HERE/value['gif'])
    assert image.n_frames>3 and image.info['loop']==0
    duration=0
    for frame in range(image.n_frames):
        image.seek(frame);duration+=image.info.get('duration',0)
    assert abs(duration/1000-value['planned_duration'])<.15,(name,duration)
    print(f'{name}: {duration/1000:.2f}s, {image.n_frames} frames, original GIF embedded')
print('PASS: 7 main slides + divider + 7 appendices; 4 GIFs; 15 PDF pages; notes and manual advancement; 118s plan.')
