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
src = out / 'Master_02_Procedure_patterns_stacked_vector_revised.pdf'
dst = out / 'Master_02_Procedure_patterns_stacked_vector_bold_titles.pdf'
r = PdfReader(src)
p = r.pages[0]
scale = 843 / 1910
pdfmetrics.registerFont(TTFont('ArialBold', historical_path('fonts/Arial Bold.ttf')))
buf = io.BytesIO()
c = canvas.Canvas(buf, pagesize=(float(p.mediabox.width), float(p.mediabox.height)))
c.scale(scale, scale)
c.setFillColorRGB(0, 0, 0)
titles = [('Profile similarity', 190, 2345, 36), ('Procedure evidence and calendar-year observed/predicted profile', 430, 2328.79, 36), ('Direction, burden and statistical evidence', 245, 1166.584, 36), ('Adjusted late / early incidence comparisons', 1057, 1166.584, 36)]
for text, x, y, size in titles:
    c.setFont('ArialBold', size)
    if text == 'Profile similarity':
        c.drawString(x, y, 'Profile')
        c.drawString(x, y - 39, 'similarity')
    else:
        c.drawString(x, y, text)
c.save()
buf.seek(0)
overlay = PdfReader(buf)
op = overlay.pages[0]
cs = ContentStream(op.get_contents(), overlay)
fonts = op['/Resources']['/Font']
unused = [k for k, f in fonts.items() if f.get_object().get('/BaseFont') == '/Helvetica']
cs.operations = [(a, o) for a, o in cs.operations if not (o == b'Tf' and a[0] in unused)]
for k in unused:
    del fonts[k]
op[NameObject('/Contents')] = cs
p.merge_page(op)
w = PdfWriter()
w.add_page(p)
w.add_metadata({'/Title': 'Procedure patterns - final stacked vector figure', '/Subject': 'Four panel titles enlarged to 36-point native Arial Bold in black; wider margins, enlarged axis text and spaced legend retained.'})
with open(dst, 'wb') as f:
    w.write(f)
text = PdfReader(dst).pages[0].extract_text()
for t, _, _, _ in titles:
    assert t.replace(' ', '') in ''.join(text.split()), t
for t in ['All 28 procedures and 72,854 reports.', 'Procedure patterns and directions of change', 'Do procedures share recurrent', 'Where do procedure SSI incidence']:
    assert t not in text, t
assert not any((c in text for c in '\u2010\u2011\u2012\u2013\u2014\u2015\u2212\ufe58\ufe63\uff0d'))
print(dst)
