# Archived editorial source. See docs/FIGURES.md. Path constants adapted; scientific values unchanged.
from _paths import historical_path
import io, json
from pathlib import Path
from pypdf import PdfReader, PdfWriter, Transformation
from pypdf.generic import ContentStream, NameObject, FloatObject, RectangleObject
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT = Path(historical_path('workspace'))
OUT = ROOT / 'outputs/pathogen-profiles-vector'
OUT.mkdir(parents=True, exist_ok=True)
SRC = Path(historical_path('project/Figures_MAINTEXT/Fig 12.pdf'))
r = PdfReader(SRC)
p = r.pages[0]
s = ContentStream(p.get_contents(), r)
groups = []
cur = None
for i, (a, o) in enumerate(s.operations):
    if o == b'BT':
        cur = {'start': i, 'text': ''}
    if cur is not None and o == b'Tj':
        cur['text'] += str(a[0])
    if o == b'ET':
        cur['end'] = i
        groups.append(cur)
        cur = None
expected = ['a.', 'Composition groups and later profile projections', 'b.', 'Later organ/space involvement by source profile', 'c.', 'Later pathogen composition of the frozen groups', 'd.', 'Later methicillin resistance within ', 'S. aureus']
last = groups[-9:]
assert [g['text'] for g in last] == expected, [g['text'] for g in last]
overall = [g for g in groups if g['text'] == 'Historical SSI pathogen profiles and later depth and resistance patterns']
assert len(overall) == 1
skip = {i for g in last + overall for i in range(g['start'], g['end'] + 1)}

def geometry(ops):
    result = []
    bt = False
    for a, o in ops:
        if o == b'BT':
            bt = True
        if not bt:
            result.append((a, o))
        if o == b'ET':
            bt = False
    return result
before = geometry(s.operations)
s.operations = [(a, o) for i, (a, o) in enumerate(s.operations) if i not in skip]
assert before == geometry(s.operations)
p[NameObject('/Contents')] = s
pdfmetrics.registerFont(TTFont('ArialBold', historical_path('fonts/Arial Bold.ttf')))
pdfmetrics.registerFont(TTFont('ArialBoldItalic', historical_path('fonts/Arial Bold Italic.ttf')))
W, H = (float(p.mediabox.width), float(p.mediabox.height))
b = io.BytesIO()
c = canvas.Canvas(b, pagesize=(W, H))
c.setFillColorRGB(0, 0, 0)
headers = [('a.', 38, 85, 947, 'Composition groups and later profile projections'), ('b.', 960, 1010, 947, 'Later organ/space involvement by source profile'), ('c.', 38, 85, 462, 'Later pathogen composition of the frozen groups'), ('d.', 960, 1010, 462, 'Later methicillin resistance within S. aureus')]
for letter, lx, tx, y, title in headers:
    c.setFont('ArialBold', 35)
    c.drawString(lx, y, letter)
    c.setFont('ArialBold', 25)
    if letter == 'd.':
        phrase = 'Later methicillin resistance within '
        c.drawString(tx, y, phrase)
        c.setFont('ArialBoldItalic', 25)
        c.drawString(tx + pdfmetrics.stringWidth(phrase, 'ArialBold', 25), y, 'S. aureus')
    else:
        c.drawString(tx, y, title)
    assert tx + pdfmetrics.stringWidth(title, 'ArialBold', 25) < 1645
c.save()
b.seek(0)
overlay = PdfReader(b)
op = overlay.pages[0]
fonts = op['/Resources']['/Font']
unused = [k for k, f in fonts.items() if f.get_object().get('/BaseFont') == '/Helvetica']
cs = ContentStream(op.get_contents(), overlay)
cs.operations = [(a, o) for a, o in cs.operations if not (o == b'Tf' and a[0] in unused)]
for k in unused:
    del fonts[k]
op[NameObject('/Contents')] = cs
p.merge_page(op)
w = PdfWriter()
w.add_page(p)
with (ROOT / 'work/fig12-compact-native.pdf').open('wb') as f:
    w.write(f)
H = 1004
scale = 843 / W
p.add_transformation(Transformation().scale(scale))
p.mediabox = RectangleObject([0, 0, W * scale, H * scale])
p.cropbox = RectangleObject([0, 0, W * scale, H * scale])
w = PdfWriter()
w.add_page(p)
w.add_metadata({'/Title': 'Figure 12 - compact panel labels and true vector artwork', '/Subject': 'Smaller bold panel labels with single-line titles; overall figure title removed; all scientific geometry retained; S. aureus remains italicized.'})
dst = OUT / 'Fig_12_compact_labels_true_vector.pdf'
with dst.open('wb') as f:
    w.write(f)
new = PdfReader(dst)
assert not len(new.pages[0].images)
t = new.pages[0].extract_text()
assert all((v in t for v in ['a.', 'b.', 'c.', 'd.', 'Composition groups and', 'later profile projections', 'Later organ/space involvement', 'by source profile', 'Later pathogen composition', 'of the frozen groups', 'Later methicillin resistance', 'within ', 'S. aureus']))
assert 'Historical SSI pathogen profiles and later depth and resistance patterns' not in t
assert not any((c in t for c in '\u2010\u2011\u2012\u2013\u2014\u2015\u2212\ufe58\ufe63\uff0d'))
(ROOT / 'work/fig12-compact-verification.json').write_text(json.dumps({'source': str(SRC), 'output': str(dst), 'source_nontext_geometry_unchanged': True, 'geometry_operation_count': len(before), 'panel_letters_pt': 35 * scale, 'title_size_pt': 25 * scale, 'overall_title_removed': True, 'panel_titles_single_line': True, 'font': 'Arial Bold', 'species_font': 'Arial Bold Italic', 'pdf_images': 0, 'ascii_dash_audit': 'passed', 'page_dimensions_pt': [W * scale, H * scale]}, indent=2))
print(dst)
