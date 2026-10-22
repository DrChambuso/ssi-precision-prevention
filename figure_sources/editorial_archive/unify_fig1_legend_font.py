# Archived editorial source. See docs/FIGURES.md. Path constants adapted; scientific values unchanged.
from _paths import historical_path
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, NameObject
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io, json, hashlib
ROOT = Path(historical_path('workspace'))
out = ROOT / 'outputs/combined-figure-vector-bold'
src = out / 'Fig_1_combined_bold_labels_true_vector.pdf'
dst = out / 'Fig_1_combined_consistent_fonts_true_vector.pdf'
r = PdfReader(src)
p = r.pages[0]
s = ContentStream(p.get_contents(), r)
source_forms = {k: hashlib.sha256(x.get_object().get_data()).hexdigest() for k, x in p['/Resources']['/XObject'].items()}
indices = [i for i, (a, o) in enumerate(s.operations) if o == b're' and len(a) == 4 and (abs(float(a[0]) - 22.56) < 0.001) and (abs(float(a[1]) - 29.52002) < 0.001)]
assert len(indices) == 1
start = indices[0] - 1
assert s.operations[start][1] == b'q'
depth = 0
for j in range(start, len(s.operations)):
    o = s.operations[j][1]
    if o == b'q':
        depth += 1
    elif o == b'Q':
        depth -= 1
    if depth == 0:
        end = j
        break
assert end - start > 2000
s.operations = s.operations[:start] + s.operations[end + 1:]
p[NameObject('/Contents')] = s
pdfmetrics.registerFont(TTFont('ArialBold', historical_path('fonts/Arial Bold.ttf')))
b = io.BytesIO()
c = canvas.Canvas(b, pagesize=(612, 1008))
c.setFont('ArialBold', 16)
entries = [('Current report at/below predicted', (0.6509804, 0.8078431, 0.8901961), 20, 40, 59), ('Above after prior at/below', (0.1411765, 0.4627451, 0.7098039), 20, 40, 39), ('Above in two consecutive years', (0.4745098, 0.3372549, 0.6588235), 318, 338, 59), ('Above with prior year unavailable', (0.7098039, 0, 0.0627451), 318, 338, 39)]
for text, col, kx, tx, y in entries:
    c.setFillColorRGB(*col)
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.7)
    c.rect(kx, y + 1.7, 9.069987, 7.93625, fill=1, stroke=1)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(tx, y, text)
    assert tx + pdfmetrics.stringWidth(text, 'ArialBold', 16) < 594
c.save()
b.seek(0)
o = PdfReader(b)
op = o.pages[0]
cs = ContentStream(op.get_contents(), o)
fonts = op['/Resources']['/Font']
unused = [k for k, f in fonts.items() if f.get_object().get('/BaseFont') == '/Helvetica']
cs.operations = [(a, o) for a, o in cs.operations if not (o == b'Tf' and a[0] in unused)]
for k in unused:
    del fonts[k]
op[NameObject('/Contents')] = cs
p.merge_page(op)
w = PdfWriter()
w.add_page(p)
w.add_metadata({'/Title': 'Figure 1 - consistent bold fonts and true vector charts', '/Subject': 'Panel b colour-key labels use the same 16-point Arial Bold font and black colour as both panel titles.'})
with dst.open('wb') as f:
    w.write(f)
r = PdfReader(dst)
p = r.pages[0]
final_forms = {k: hashlib.sha256(x.get_object().get_data()).hexdigest() for k, x in p['/Resources']['/XObject'].items()}
assert final_forms == source_forms
assert not len(p.images)
t = p.extract_text()
assert all((e[0] in t for e in entries))
assert not any((x in t for x in '\u2010\u2011\u2012\u2013\u2014\u2015\u2212\ufe58\ufe63\uff0d'))
report = {'font': 'Arial Bold', 'panel_title_and_legend_font_size_pt': 16, 'panel_letters_size_pt': 23, 'chart_vector_forms_unchanged': True, 'pdf_raster_images': 0, 'legend_text': [e[0] for e in entries], 'ascii_dash_audit': 'passed'}
(ROOT / 'work/fig1-consistent-font-verification.json').write_text(json.dumps(report, indent=2))
print(dst)
