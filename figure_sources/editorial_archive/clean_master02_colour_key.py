# Archived editorial source. See docs/FIGURES.md. Path constants adapted; scientific values unchanged.
from _paths import historical_path
import io, json
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, NameObject
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
root = Path(historical_path('workspace'))
out = root / 'outputs/procedure-patterns-vector-revised'
src = out / 'Master_02_Procedure_patterns_stacked_vector_bold_titles.pdf'
dst = out / 'Master_02_Procedure_patterns_stacked_vector_clean_colour_key.pdf'
r = PdfReader(src)
p = r.pages[0]
scale = 843 / 1910
pdfmetrics.registerFont(TTFont('ArialBold', historical_path('fonts/Arial Bold.ttf')))
b = io.BytesIO()
c = canvas.Canvas(b, pagesize=(float(p.mediabox.width), float(p.mediabox.height)))
c.scale(scale, scale)
c.setFillColorRGB(0.137255, 0.196078, 0.243137)
c.setFont('ArialBold', 22)
c.drawString(370, 1267, 'Observed / predicted SSI ratio:')
keys = [(740, (0.714, 0.847, 0.925), '<=0.75'), (1000, (0.859, 0.918, 0.957), '>0.75 to 1.00'), (1260, (0.918, 0.725, 0.725), '>1.00 to 1.25'), (1520, (0.722, 0.122, 0.196), '>1.25')]
for x, color, label in keys:
    c.setFillColorRGB(*color)
    c.rect(x, 1264, 30, 21, fill=1, stroke=0)
    c.setFillColorRGB(0.137255, 0.196078, 0.243137)
    c.drawString(x + 42, 1267, label)
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
w.add_metadata({'/Title': 'Procedure patterns - stacked vector figure with colour key', '/Subject': 'Colour ratio key retained below panel b; duplicate explanatory line removed; vector charts and enlarged panel titles preserved.'})
with open(dst, 'wb') as f:
    w.write(f)
text = PdfReader(dst).pages[0].extract_text()
assert 'Observed / predicted SSI ratio:' in text
assert '>0.75 to 1.00' in text
assert '>1.00 to 1.25' in text
assert '1.00 = as predicted.' not in text
assert 'At least 25% of reports' not in text
assert not any((c in text for c in '\u2010\u2011\u2012\u2013\u2014\u2015\u2212\ufe58\ufe63\uff0d'))
print(dst)
