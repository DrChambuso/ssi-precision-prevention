# Archived editorial source. See docs/FIGURES.md. Path constants adapted; scientific values unchanged.
from _paths import historical_path
import io, json, math, pathlib
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, TextStringObject
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
O = pathlib.Path(historical_path('workspace/work/supplement_vector_audit'))
D = O / 'cleaned'
W = 183 * 72 / 25.4
for nm, fn in [('Arial', 'Arial.ttf'), ('Arial-Bold', 'Arial Bold.ttf')]:
    pdfmetrics.registerFont(TTFont(nm, historical_path('fonts/') + fn))

def bt_items(p):
    b = []
    out = []
    for a, o in ContentStream(p.get_contents(), p.pdf).operations:
        if o == b'BT':
            b = []
        b.append((a, o))
        if o == b'ET':
            txt = ''.join((str(a[-1]) if o == b'Tj' else ''.join((str(v) for v in a[0] if isinstance(v, (str, TextStringObject)))) if o == b'TJ' else '' for a, o in b)).strip()
            tm = next((a for a, o in b if o == b'Tm'), None)
            if tm:
                out.append((txt, float(tm[4]), float(tm[5])))
    return out
p = PdfReader(D / 'native/Supplementary_Figure_S05_native.pdf').pages[0]
items = bt_items(p)
names = sorted([r for r in items if r[0].startswith(tuple(('P%02d ' % i for i in range(1, 29))))], key=lambda x: -x[2])
rows = []
for t, x, y in names:
    est = [a for a, xx, yy in items if 900 < xx < 1040 and abs(yy - y) < 2.1]
    q = [a for a, xx, yy in items if xx > 1040 and abs(yy - y) < 2.1]
    assert len(est) == len(q) == 1, (t, est, q)
    rows.append([t, est[0], q[0].lstrip('=')])
assert len(rows) == 28
(O / 'S05_verified_table.json').write_text(json.dumps(rows, indent=2))
buf = io.BytesIO()
c = canvas.Canvas(buf, pagesize=(W, 360))
c.setFillColorRGB(0, 0, 0)
c.setFont('Arial-Bold', 8)
c.drawString(10, 342, 'b.')
c.setFont('Arial-Bold', 7)
c.drawString(23, 342, 'Adjusted late / early incidence comparisons')
xs = [10, 290, 440]
c.setFont('Arial-Bold', 6.5)
for x, t in zip(xs, ['Procedure', 'aIRR (95% CI)', 'BH q']):
    c.drawString(x, 322, t)
for i, row in enumerate(rows):
    y = 305 - i * 10.4
    if i % 2 == 0:
        c.setFillColorRGB(0.945, 0.953, 0.961)
        c.rect(8, y - 2.4, W - 16, 10.4, stroke=0, fill=1)
    c.setFillColorRGB(0, 0, 0)
    for j, (x, t) in enumerate(zip(xs, row)):
        c.setFont('Arial-Bold' if j == 0 else 'Arial', 6.3 if j == 0 else 6.5)
        c.drawString(x, y, t)
c.save()
newpage = PdfReader(io.BytesIO(buf.getvalue())).pages[0]
path = D / 'Supplementary_Figure_S05_vector.pdf'
r = PdfReader(path)
w = PdfWriter()
w.add_page(r.pages[0])
w.add_page(newpage)
for pp in w.pages:
    pp.compress_content_streams()
with path.open('wb') as f:
    w.write(f)
rows18 = [['10%', '26.2', '25.3', '+0.89 (-0.20 to 1.74)', '0.075; 0.075'], ['20%', '46.0', '43.6', '+2.39 (1.37 to 3.54)', '<0.001; <0.001'], ['30%', '62.7', '56.6', '+6.11 (3.79 to 8.32)', '<0.001; <0.001']]
(O / 'S18_verified_table.json').write_text(json.dumps(rows18, indent=2))
buf = io.BytesIO()
c = canvas.Canvas(buf, pagesize=(W, 130))
c.setFillColorRGB(0, 0, 0)
c.setFont('Arial-Bold', 8)
c.drawString(10, 112, 'c.')
c.setFont('Arial-Bold', 7)
c.drawString(23, 112, 'Added signal capture versus prior SSI counts')
xs = [10, 65, 145, 230, 425]
heads = [['Review', 'capacity'], ['Model', 'capture (%)'], ['Prior-count', 'capture (%)'], ['Added capture, percentage points', '(95% CI)'], ['P; BH q', '(3 capacities)']]
for x, ls in zip(xs, heads):
    c.setFont('Arial-Bold', 6)
    for j, t in enumerate(ls):
        c.drawString(x, 91 - j * 7.2, t)
for i, row in enumerate(rows18):
    y = 66 - i * 18
    if i % 2 == 0:
        c.setFillColorRGB(0.945, 0.953, 0.961)
        c.rect(8, y - 4, W - 16, 18, stroke=0, fill=1)
    c.setFillColorRGB(0, 0, 0)
    c.setFont('Arial', 6.5)
    for x, t in zip(xs, row):
        c.drawString(x, y, t)
c.save()
page = PdfReader(io.BytesIO(buf.getvalue())).pages[0]
path = D / 'Supplementary_Figure_S18_vector.pdf'
r = PdfReader(path)
assert len(r.pages) == 3, len(r.pages)
w = PdfWriter()
w.add_page(r.pages[0])
w.add_page(r.pages[1])
w.add_page(page)
for pp in w.pages:
    pp.compress_content_streams()
with path.open('wb') as f:
    w.write(f)
meta = json.loads((O / 'cleaned_layout_manifest.json').read_text())
for a in meta:
    if a['number'] in [5, 18]:
        idx = 1 if a['number'] == 5 else 2
        h = 360 if a['number'] == 5 else 130
        a['pages'][idx]['height_pt'] = h
        a['pages'][idx]['tiles'] = []
        a['pages'][idx]['recreated_table'] = 'Verified native source values, editable vector text, no data changes.'
(O / 'cleaned_layout_manifest.json').write_text(json.dumps(meta, indent=2))
print('S5b and S18c tables verified and rebuilt at readable size.')
