# Archived editorial source. See docs/FIGURES.md. Path constants adapted; scientific values unchanged.
from _paths import historical_path
from pathlib import Path
import io, json, hashlib
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, ContentStream
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT = Path(historical_path('workspace'))
out = ROOT / 'outputs/combined-figure-vector-bold'
out.mkdir(parents=True, exist_ok=True)
src = ROOT / 'outputs/combined-figure-vector/Fig_1_combined_true_vector.pdf'
dst = out / 'Fig_1_combined_bold_labels_true_vector.pdf'
r = PdfReader(src)
p = r.pages[0]
cs = ContentStream(p.get_contents(), r)
original_forms = {k: hashlib.sha256(v.get_object().get_data()).hexdigest() for k, v in p['/Resources']['/XObject'].items()}
ops = []
inside = False
removed = 0
for a, o in cs.operations:
    if o == b'BT':
        inside = True
        removed += 1
    if not inside:
        ops.append((a, o))
    if o == b'ET':
        inside = False
cs.operations = ops
p[NameObject('/Contents')] = cs
pdfmetrics.registerFont(TTFont('ArialBold', historical_path('fonts/Arial Bold.ttf')))
b = io.BytesIO()
c = canvas.Canvas(b, pagesize=(612, 1008))
c.setFillColorRGB(0, 0, 0)
headers = [('a.', 'Procedure-specific SSI incidence and burden', 13, 975.12), ('b.', 'SSI burden by current and preceding annual reports', 13, 496.56)]
for letter, title, x, y in headers:
    c.setFont('ArialBold', 23)
    c.drawString(x, y, letter)
    c.setFont('ArialBold', 16)
    c.drawString(x + 31, y, title)
    assert x + 31 + pdfmetrics.stringWidth(title, 'ArialBold', 16) < 592
c.save()
b.seek(0)
overlay = PdfReader(b)
op = overlay.pages[0]
f = op['/Resources']['/Font']
unused = [k for k, x in f.items() if x.get_object().get('/BaseFont') == '/Helvetica']
ocs = ContentStream(op.get_contents(), overlay)
ocs.operations = [(a, o) for a, o in ocs.operations if not (o == b'Tf' and a[0] in unused)]
for k in unused:
    del f[k]
op[NameObject('/Contents')] = ocs
p.merge_page(op)
w = PdfWriter()
w.add_page(p)
w.add_metadata({'/Title': 'Figure 1 - combined vector figure with bold panel labels and titles', '/Subject': 'Arial Bold panel letters and titles matched to Master 2; source scientific vector artwork retained unchanged.'})
with dst.open('wb') as f:
    w.write(f)
n = PdfReader(dst)
pg = n.pages[0]
final_forms = {k: hashlib.sha256(v.get_object().get_data()).hexdigest() for k, v in pg['/Resources']['/XObject'].items()}
assert original_forms == final_forms
assert len(pg.images) == 0
text = pg.extract_text()
assert all((t in text for _, t, _, _ in headers))
assert not any((c in text for c in '\u2010\u2011\u2012\u2013\u2014\u2015\u2212\ufe58\ufe63\uff0d'))
(ROOT / 'work/fig1-bold-verification.json').write_text(json.dumps({'source_vector_form_hashes': original_forms, 'source_vector_forms_unchanged': True, 'images': 0, 'panel_letter_size_pt': 23, 'title_size_pt': 16, 'font': 'Arial Bold', 'removed_old_text_blocks': removed, 'headers': headers, 'ascii_dash_audit': 'passed'}, indent=2))
print(dst)
