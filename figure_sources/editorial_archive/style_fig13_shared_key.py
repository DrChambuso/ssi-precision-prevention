# Archived editorial source. See docs/FIGURES.md. Path constants adapted; scientific values unchanged.
from _paths import historical_path
import io, json
from pathlib import Path
from collections import Counter
from pypdf import PdfReader, PdfWriter, Transformation
from pypdf.generic import ContentStream, NameObject, RectangleObject
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT = Path(historical_path('workspace'))
OUT = ROOT / 'outputs/resistance-phenotypes-vector'
OUT.mkdir(parents=True, exist_ok=True)
SRC = Path(historical_path('project/Figures_MAINTEXT/Fig 13.pdf'))
r = PdfReader(SRC)
p = r.pages[0]
s = ContentStream(p.get_contents(), r)
groups = []
g = None
for i, (a, o) in enumerate(s.operations):
    if o == b'BT':
        g = {'start': i, 'text': ''}
    if g is not None and o == b'Tj':
        g['text'] += str(a[0])
    if o == b'ET':
        g['end'] = i
        groups.append(g)
        g = None
key = next((g for g in groups if g['text'] == 'Phenotype (%)'))
keystart = key['start'] - 1
assert s.operations[keystart][1] == b'rg'
keyrects = []
color = None
for a, o in s.operations[key['end'] + 1:]:
    if o == b'rg':
        color = [float(v) for v in a]
    if o == b're':
        keyrects.append((color, [float(v) for v in a]))
assert len(keyrects) == 200
remove = {'Which resistant phenotypes should procedure-specific stewardship reviews verify locally?', 'A  Adults, 2015-2017', 'B  Adults, 2018-2021', 'C  Pediatrics, 2015-2017', 'D  Pediatrics, 2018-2021'}
skip = {i for g in groups if g['text'] in remove for i in range(g['start'], g['end'] + 1)}
assert {g['text'] for g in groups if g['text'] in remove} == remove
bodyops = s.operations[:keystart]

def geometry(ops):
    out = []
    bt = False
    for a, o in ops:
        if o == b'BT':
            bt = True
        if not bt:
            out.append((a, o))
        if o == b'ET':
            bt = False
    return out
before = geometry(bodyops)
s.operations = [(a, o) for i, (a, o) in enumerate(bodyops) if i not in skip]
assert geometry(s.operations) == before
p[NameObject('/Contents')] = s
fonts = p['/Resources']['/Font']
unused = [k for k, f in fonts.items() if f.get_object().get('/BaseFont') == '/Helvetica']
s.operations = [(a, o) for a, o in s.operations if not (o == b'Tf' and a[0] in unused)]
for k in unused:
    del fonts[k]
pdfmetrics.registerFont(TTFont('ArialBold', historical_path('fonts/Arial Bold.ttf')))

def read_overlay(buf):
    rr = PdfReader(buf)
    op = rr.pages[0]
    cs = ContentStream(op.get_contents(), rr)
    f = op['/Resources']['/Font']
    unused = [k for k, x in f.items() if x.get_object().get('/BaseFont') == '/Helvetica']
    cs.operations = [(a, o) for a, o in cs.operations if not (o == b'Tf' and a[0] in unused)]
    for k in unused:
        del f[k]
    op[NameObject('/Contents')] = cs
    return op
b = io.BytesIO()
c = canvas.Canvas(b, pagesize=(1440, 1152))
c.setFillColorRGB(0, 0, 0)
headers = [('a.', 'Adults, 2015-2017', 30, 72, 1084), ('b.', 'Adults, 2018-2021', 735, 777, 1084), ('c.', 'Pediatrics, 2015-2017', 30, 72, 544), ('d.', 'Pediatrics, 2018-2021', 735, 777, 544)]
for letter, text, lx, tx, y in headers:
    c.setFont('ArialBold', 30.1)
    c.drawString(lx, y, letter)
    c.setFont('ArialBold', 21.5)
    c.drawString(tx, y, text)
c.save()
b.seek(0)
p.merge_page(read_overlay(b))
w = PdfWriter()
w.add_page(p)
with (ROOT / 'work/fig13-body-native.pdf').open('wb') as f:
    w.write(f)
shift = 110
H = 1248
p.add_transformation(Transformation().translate(0, shift))
p.mediabox = RectangleObject([0, 0, 1440, H])
p.cropbox = RectangleObject([0, 0, 1440, H])
b = io.BytesIO()
c = canvas.Canvas(b, pagesize=(1440, H))
c.setFillColorRGB(0, 0, 0)
c.setFont('ArialBold', 21.5)
c.drawCentredString(720, 86, 'Phenotype (%)')
for color, (x, y, w, h) in keyrects:
    c.setFillColorRGB(*color)
    c.rect(470 + (x - 1110) * 500 / 300, 55, w * 500 / 300, 14, fill=1, stroke=0)
c.setFillColorRGB(0, 0, 0)
c.setFont('ArialBold', 16.5)
for v in [0, 25, 50, 75, 100]:
    c.drawCentredString(470 + v * 5, 30, str(v))
c.save()
b.seek(0)
p.merge_page(read_overlay(b))
scale = 843 / 1440
p.add_transformation(Transformation().scale(scale))
p.mediabox = RectangleObject([0, 0, 843, H * scale])
p.cropbox = RectangleObject([0, 0, 843, H * scale])
w = PdfWriter()
w.add_page(p)
w.add_metadata({'/Title': 'Figure 13 - compact labels and shared phenotype colour key', '/Subject': 'Overall heading removed; lower-case Arial Bold panel headings; shared 0-100 phenotype percentage colour key centered below all four panels. Source cell values and heatmap artwork retained.'})
dst = OUT / 'Fig_13_compact_labels_shared_key_true_vector.pdf'
with dst.open('wb') as f:
    w.write(f)
r2 = PdfReader(dst)
pg = r2.pages[0]
t = pg.extract_text()
assert not len(pg.images)
assert 'Which resistant phenotypes should procedure-specific stewardship reviews verify locally?' not in t
assert t.count('Phenotype (%)') == 1
assert all((label in t for label in ['a.', 'b.', 'c.', 'd.']))
assert not any((c in t for c in '\u2010\u2011\u2012\u2013\u2014\u2015\u2212\ufe58\ufe63\uff0d'))
celltexts = [g['text'] for g in groups if g['end'] < keystart and g['text'] not in remove and g['text'].strip()]
for txt in celltexts:
    assert txt in t, txt
report = {'source': str(SRC), 'output': str(dst), 'source_heatmap_geometry_unchanged': True, 'cell_text_entries_preserved': len(celltexts), 'shared_key': 'Phenotype (%)', 'shared_scale': [0, 100], 'original_gradient_steps_preserved': len(keyrects), 'overall_title_removed': True, 'panel_letter_size_pt': 30.1 * scale, 'panel_title_size_pt': 21.5 * scale, 'font': 'Arial Bold', 'pdf_images': 0, 'ascii_dash_audit': 'passed', 'page_dimensions_pt': [843, H * scale]}
(ROOT / 'work/fig13-verification.json').write_text(json.dumps(report, indent=2))
print(dst)
