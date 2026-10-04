"""Build a static PPTX with one image per slide, manual advancement and French notes.
Run via uv --no-project --with python-pptx python build_pptx.py in docs/pitch.
"""
import argparse
from copy import deepcopy
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile
from lxml import etree
from pptx import Presentation
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Emu
HERE=Path(__file__).resolve().parent
WIDTH,HEIGHT=Emu(12192000),Emu(6858000)
slides=json.loads((HERE/'slides/slides.json').read_text())
parser=argparse.ArgumentParser()
parser.add_argument('--refresh-images',action='store_true',help='Update slide PNGs in an existing PPTX, preserving all other contents, including edited notes.')
parser.add_argument('--insert-slide',type=int,help='Insert one source slide into the existing PPTX at this 1-based position, preserving other slides and notes.')
parser.add_argument('--update-notes',type=int,nargs='*',default=[],help='Existing slide positions whose notes should follow the updated source when inserting.')
args=parser.parse_args()
output=HERE/'Club-des-Affaires-pitch.pptx'
temporary=HERE/'.build/pitch-export.pptx'
temporary.parent.mkdir(exist_ok=True)
if args.refresh_images or args.insert_slide:
    original=output.read_bytes()
    deck=Presentation(BytesIO(original))
    old_slides=list(deck.slides)
    if args.insert_slide and args.refresh_images:
        raise SystemExit('Choose insertion or image refresh.')
    insert=args.insert_slide-1 if args.insert_slide else None
    if len(old_slides)+(insert is not None)!=len(slides) or (insert is not None and not 0<=insert<len(slides)):
        raise SystemExit('Slide count changed; refusing to overwrite an edited presentation.')
    updated_notes=set(args.update_notes)
    if updated_notes and (insert is None or not updated_notes<=set(range(1,len(old_slides)+1))):
        raise SystemExit('Note updates require valid existing slide positions and insertion.')
    old_partnames=[str(slide.part.partname) for slide in old_slides]
    additions={}
    xml_updates={}
    if insert is not None:
        info=slides[insert]
        new_slide=deck.slides.add_slide(deck.slide_layouts[6])
        new_slide.shapes.add_picture(str(HERE/info['image']),0,0,WIDTH,HEIGHT)
        transition=OxmlElement('p:transition');transition.set('advClick','1')
        new_slide._element.insert_element_before(transition,'p:timing','p:extLst')
        new_notes=new_slide.notes_slide
        if new_notes.notes_text_frame is None:
            # PowerPoint can remove the body placeholder from the notes master.
            # Existing note slides still have it: copy its layout for the inserted slide.
            body=deepcopy(old_slides[0].notes_slide.notes_placeholder._element)
            body.xpath('.//p:cNvPr')[0].set('id',str(max((shape.shape_id for shape in new_notes.shapes),default=0)+1))
            new_notes.shapes._spTree.insert_element_before(body,'p:extLst')
        new_notes.notes_text_frame.text=info['notes']
        slide_id=deck.slides._sldIdLst[-1]
        deck.slides._sldIdLst.remove(slide_id);deck.slides._sldIdLst.insert(insert,slide_id)
        for position in updated_notes:
            index=position-1
            old_slides[index].notes_slide.notes_text_frame.text=slides[index+(index>=insert)]['notes']
        generated=BytesIO();deck.save(generated)
        if [str(slide.part.partname) for slide in old_slides]!=old_partnames:
            raise SystemExit('Existing slide parts were renamed; original presentation preserved.')
        with ZipFile(BytesIO(original)) as source, ZipFile(generated) as expanded:
            additions={name:expanded.read(name) for name in expanded.namelist() if name not in source.namelist()}
            control_files=['[Content_Types].xml','ppt/presentation.xml','ppt/_rels/presentation.xml.rels']
            control_files += [str(old_slides[p-1].notes_slide.part.partname).lstrip('/') for p in updated_notes]
            xml_updates={name:expanded.read(name) for name in control_files}
            # Keep PowerPoint's other application properties; update its slide count only.
            app=etree.fromstring(source.read('docProps/app.xml'))
            count=app.find('{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}Slides')
            if count is not None:
                count.text=str(len(slides))
                xml_updates['docProps/app.xml']=etree.tostring(app,xml_declaration=True,encoding='UTF-8',standalone=True)
    replacements={}
    for index,slide in enumerate(old_slides):
        info=slides[index+(insert is not None and index>=insert)]
        if len(slide.shapes)!=1 or not hasattr(slide.shapes[0],'image'):
            raise SystemExit('Slide structure changed; refusing to overwrite an edited slide.')
        shape=slide.shapes[0]
        image_part=slide.part.related_part(shape._element.blipFill.blip.rEmbed)
        name=str(image_part.partname).lstrip('/')
        data=(HERE/info['image']).read_bytes()
        if name in replacements and replacements[name]!=data:
            raise SystemExit('Shared image has conflicting replacements.')
        replacements[name]=data
    with ZipFile(BytesIO(original)) as source:
        changed={name:data for name,data in replacements.items() if source.read(name)!=data}
        changed.update(xml_updates)
        with ZipFile(temporary,'w') as target:
            target.comment=source.comment
            for entry in source.infolist():
                target.writestr(entry,changed.get(entry.filename,source.read(entry.filename)))
            for name,data in additions.items():
                target.writestr(name,data,compress_type=8)
    if output.read_bytes()!=original:
        temporary.unlink()
        raise SystemExit('PowerPoint changed during export; original file preserved. Close/save it and retry.')
    (HERE/'.build/pitch-before-image-refresh.pptx').write_bytes(original)
    temporary.replace(output)
    print(f'{output.name}: {len(deck.slides)} slides; {len(replacements)} source images refreshed; {len(additions)} added parts; notes preserved except explicitly updated positions {sorted(updated_notes)}')
    raise SystemExit(0)
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
deck.save(temporary)
temporary.replace(output)
print(f'{output.name}: {len(slides)} static slides and French notes')
