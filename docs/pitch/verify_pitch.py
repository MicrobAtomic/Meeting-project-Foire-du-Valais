"""Validate static exports, the requested screen order and notes without changing the app."""
import argparse
import json
from pathlib import Path
import re
from zipfile import ZipFile
from PIL import Image
from pptx import Presentation
HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--preserved-pptx',type=Path,help='Original edited PPTX: check that everything except slide PNGs was preserved.')
args=parser.parse_args()
slides=json.loads((HERE/'slides/slides.json').read_text())
story=json.loads((HERE/'story.json').read_text())
captures=json.loads((HERE/'screens/manifest.json').read_text())
deck=Presentation(HERE/'Club-des-Affaires-pitch.pptx')
assert len(slides)==len(deck.slides)==26
assert len(story)==18 and sum(s['seconds'] for s in story)==118
assert len(re.findall(rb'/Type\s*/Page\b',(HERE/'Club-des-Affaires-pitch.pdf').read_bytes()))==26
assert story[0]['screen']=='screens/web/000.png'
assert [(r['id'],r['screen']) for r in story[2:6]]==[
    ('web-login','screens/web/001.png'),('web-dashboard','screens/web/002.png'),
    ('web-album','screens/web/003.png'),('web-intros','screens/web/004.png')]
used=[r['screen'] for r in story if r['screen']]
expected=[f'screens/{name}/{frame["file"]}' for name,frames in captures['scenes'].items() for frame in frames]
assert set(used)==set(expected) and len(used)==len(set(used))==16
assert captures['errors']==[]
clock=0
for row in story:
    assert row['start']==clock and row['end']==clock+row['seconds'];clock=row['end']
for i,(row,slide) in enumerate(zip(slides,deck.slides)):
    assert Image.open(HERE/row['image']).size==(1920,1080)
    if not args.preserved_pptx:
        assert slide.notes_slide.notes_text_frame.text==row['notes']
    assert len(slide.shapes)==1 and slide.shapes[0].image.blob==(HERE/row['image']).read_bytes()
    if row['id']:
        script=story[i]
        assert row['id']==script['id'] and row['notes'].endswith(script['text'])
        assert row['seconds']==script['seconds'] and row['chapter']==script['chapter']
        assert script['text'] in (HERE.parent/'PITCH.md').read_text()
        assert [s['source'] for s in row['screens']]==([script['screen']] if script['screen'] else [])
    transition=slide._element.find('{http://schemas.openxmlformats.org/presentationml/2006/main}transition')
    assert transition is not None and transition.get('advClick','1') in ('1','true') and transition.get('advTm') is None
    assert slide._element.find('{http://schemas.openxmlformats.org/presentationml/2006/main}timing') is None
with ZipFile(HERE/'Club-des-Affaires-pitch.pptx') as archive:
    assert not any(name.endswith(('.gif','.mp4')) for name in archive.namelist())
    assert all(name.endswith('.png') for name in archive.namelist() if name.startswith('ppt/media/'))
    if args.preserved_pptx:
        with ZipFile(args.preserved_pptx) as original:
            assert archive.namelist()==original.namelist()
            media={str(slide.part.related_part(slide.shapes[0]._element.blipFill.blip.rEmbed).partname).lstrip('/') for slide in deck.slides}
            changed=[name for name in archive.namelist() if archive.read(name)!=original.read(name)]
            assert set(changed)<=media, f'Unexpected changes to the edited PPTX: {changed}'
            print(f'PASS: {len(changed)} updated slide images; all edited notes and other PPTX contents preserved byte for byte.')
print('PASS: 18 manual slides + divider + 7 appendices; 16 unique fixed screens; cover and web order; notes; 26 PDF pages; 118s plan.')
