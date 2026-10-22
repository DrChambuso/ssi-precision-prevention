# Archived editorial source. See docs/FIGURES.md. Path constants adapted; scientific values unchanged.
from _paths import historical_path
import io, json, copy, pathlib, re
from pypdf import PdfReader, PdfWriter, PageObject, Transformation
from pypdf.generic import ContentStream, NameObject, RectangleObject, TextStringObject
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
O = pathlib.Path(historical_path('workspace/work/supplement_vector_audit'))
D = O / 'cleaned'
W = 183 * 72 / 25.4
for nm, fn in [('Arial', 'Arial.ttf'), ('Arial-Bold', 'Arial Bold.ttf')]:
    if nm not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(nm, historical_path('fonts/') + fn))
meta = json.loads((O / 'cleaned_layout_manifest.json').read_text())
man = json.loads((D / 'figure_manifest.json').read_text())

def save(path, pages):
    w = PdfWriter()
    for p in pages:
        fonts = p['/Resources']['/Font']
        reg = next((v for v in fonts.values() if 'ArialMT' in str(v.get_object().get('/BaseFont', ''))), None)
        for k in list(fonts.keys()):
            if 'Helvetica' in str(fonts[k].get_object().get('/BaseFont', '')) and reg:
                fonts[k] = reg
        w.add_page(p)
        w.pages[-1].compress_content_streams()
    with path.open('wb') as f:
        w.write(f)

def canvaspage(b, H):
    return canvas.Canvas(b, pagesize=(W, H))

def join(upper, lower, croplower=None):
    low = copy.copy(lower)
    crop0 = 0
    if croplower is not None:
        crop0 = croplower
        low.cropbox = RectangleObject([0, crop0, W, float(low.mediabox.height)])
        low.mediabox = low.cropbox
    lh = float(low.mediabox.height)
    uh = float(upper.mediabox.height)
    p = PageObject.create_blank_page(width=W, height=lh + uh)
    p.merge_transformed_page(upper, Transformation().translate(0, lh))
    p.merge_transformed_page(low, Transformation().translate(0, -crop0))
    return p
for n, upperidx, loweridx, cut in [(13, 1, 2, 50), (16, 2, 3, 150), (18, 1, 2, None)]:
    path = D / f'Supplementary_Figure_S{n:02d}_vector.pdf'
    r = PdfReader(path)
    merged = join(r.pages[upperidx], r.pages[loweridx], cut)
    new = [p for i, p in enumerate(r.pages) if i not in [upperidx, loweridx]] + [merged]
    save(path, new)
    a = next((a for a in meta if a['number'] == n))
    u = a['pages'][upperidx]
    l = a['pages'][loweridx]
    a['pages'] = [p for i, p in enumerate(a['pages']) if i not in [upperidx, loweridx]] + [dict(page=len(new), width_pt=W, height_pt=float(merged.mediabox.height), headers=u['headers'] + l['headers'], tiles=[], combined_panels=True)]
    a['page_count'] = len(new)
    b = next((b for b in man if b['number'] == n))
    b['pages'] = [dict(panels=', '.join((h['label'].rstrip('.') for h in p['headers']))) for p in a['pages']]
palette = [(213 / 255, 94 / 255, 0), (0, 114 / 255, 178 / 255), (204 / 255, 121 / 255, 167 / 255), (0, 158 / 255, 115 / 255), (230 / 255, 159 / 255, 0), (0.4, 0.4, 0.4)]
family = ['Abdominal and enteric', 'Implant and orthopedic', 'Obstetric and pelvic', 'Cardiac and vascular', 'Transplant', 'Other']
for n, dy in [(1, 50), (3, 35)]:
    path = D / f'Supplementary_Figure_S{n:02d}_vector.pdf'
    r = PdfReader(path)
    old = r.pages[0]
    oldh = float(old.mediabox.height)
    H = oldh + dy
    p = PageObject.create_blank_page(width=W, height=H)
    p.merge_transformed_page(old, Transformation().translate(0, dy))
    b = io.BytesIO()
    c = canvaspage(b, H)
    sc = (W - 20) / 828
    c.setFillColorRGB(1, 1, 1)
    if n == 1:
        for x, y, w, h in [(326, 488, 90, 62), (355, 88, 65, 25)]:
            c.rect(10 + x * sc, dy + 10 + (y - 10) * sc, w * sc, h * sc, stroke=0, fill=1)
    else:
        c.rect(10 + 715 * sc, dy + 10, 113 * sc, 60 * sc, stroke=0, fill=1)
    c.setFillColorRGB(0, 0, 0)
    c.setFont('Arial-Bold', 5.5)
    c.drawString(10, dy - 8 if n == 1 else 25, 'Procedure family')
    for i, (lab, col) in enumerate(zip(family, palette)):
        x = 10 + i % 3 * (135 if n == 1 else 155)
        y = (30 if n == 1 else 14) - i // 3 * 12 if n == 1 else 14 - i // 3 * 10
        c.setFillColorRGB(*col)
        c.rect(x, y - 1, 4, 4, stroke=0, fill=1)
        c.setFillColorRGB(0, 0, 0)
        c.setFont('Arial', 5.5)
        c.drawString(x + 7, y, lab)
    if n == 1:
        c.setFont('Arial-Bold', 5.5)
        c.drawString(415, 42, 'Period')
        for y, lab, col in [(30, '2016-2018', (86 / 255, 180 / 255, 233 / 255)), (18, '2023-2025', (213 / 255, 94 / 255, 0))]:
            c.setStrokeColorRGB(*col)
            c.setFillColorRGB(*col)
            c.setLineWidth(0.6)
            c.line(415, y + 1.5, 423, y + 1.5)
            c.circle(419, y + 1.5, 1.4, stroke=0, fill=1)
            c.setFillColorRGB(0, 0, 0)
            c.setFont('Arial', 5.5)
            c.drawString(427, y, lab)
    c.save()
    p.merge_page(PdfReader(io.BytesIO(b.getvalue())).pages[0])
    save(path, [p])
    a = next((a for a in meta if a['number'] == n))
    a['pages'][0]['height_pt'] = H
    a['pages'][0]['legend_reflowed'] = True
src = PdfReader(D / 'native/Supplementary_Figure_S10_native.pdf').pages[0]
cs = ContentStream(src.get_contents(), src.pdf)
ops = cs.operations
new = []
i = 0
remove_prefix = ['No baseline SSI (n=', 'Baseline SSI at/below predicted (n=', 'Above predicted, <=2x predicted (n=', 'Above predicted, >2x predicted (n=', 'Baseline states, year 1 global', 'State 1 vs no baseline SSI:', 'State 2 vs no baseline SSI:', 'State 3 vs no baseline SSI:', 'All four groups:']
while i < len(ops):
    if ops[i][1] != b'BT':
        new.append(ops[i])
        i += 1
        continue
    j = i + 1
    while j < len(ops) and ops[j][1] != b'ET':
        j += 1
    block = ops[i:j + 1]
    txt = ''.join((str(a[-1]) if o == b'Tj' else ''.join((str(v) for v in a[0] if isinstance(v, (str, TextStringObject)))) if o == b'TJ' else '' for a, o in block)).strip()
    if txt in ['a.', 'Time to first follow-up SSI signal'] or any((txt.startswith(z) for z in remove_prefix)):
        new.extend(((a, o) for a, o in block if o in [b'cs', b'CS', b'scn', b'SCN', b'rg', b'RG', b'g', b'G']))
    else:
        new.extend(block)
    i = j + 1
cs.operations = new
src[NameObject('/Contents')] = cs
src.cropbox = RectangleObject([0, 179, 1008, 654])
src.mediabox = src.cropbox
cw = W - 10
sc = cw / 1008
H = 185 + 475 * sc + 25
p = PageObject.create_blank_page(width=W, height=H)
p.merge_transformed_page(src, Transformation().translate(0, -179).scale(sc).translate(5, 185))
b = io.BytesIO()
c = canvaspage(b, H)
c.setFillColorRGB(1, 1, 1)
c.rect(5 + 64 * sc, 185 + (236 - 179) * sc, 266 * sc, 37 * sc, stroke=0, fill=1)
c.setFillColorRGB(0, 0, 0)
c.setFont('Arial-Bold', 8)
c.drawString(10, H - 12, 'a.')
c.setFont('Arial-Bold', 7)
c.drawString(23, H - 12, 'Time to first follow-up SSI signal')
rows = [['No baseline SSI', '7,904', '5,845', '3,352', '2,225', '1,019', 'Reference', ''], ['SSI at/below predicted', '569', '359', '156', '92', '32', '1.20 (1.01-1.43)', '0.035'], ['Above predicted, <=2x predicted', '679', '342', '134', '69', '25', '1.97 (1.71-2.28)', '<0.001'], ['Above predicted, >2x predicted', '929', '575', '289', '189', '101', '2.03 (1.78-2.32)', '<0.001']]
cols = [27, 193, 227, 261, 295, 329, 375, 484]
colors = [(0.133, 0.608, 0.525), (0.929, 0.471, 0), (0.141, 0.463, 0.71), (0.808, 0.149, 0.208)]
c.setFont('Arial-Bold', 6)
c.drawString(10, 166, 'Baseline state')
c.drawCentredString(262, 166, 'Units at risk, years from baseline')
c.drawString(375, 166, 'Year 1 aHR (95% CI)')
c.drawString(484, 166, 'BH q')
for x, lab in zip(cols[1:6], ['0', '2', '4', '6', '9']):
    c.drawString(x, 155, lab)
for r, row in enumerate(rows):
    y = 139 - r * 19
    if r % 2 == 0:
        c.setFillColorRGB(0.945, 0.953, 0.961)
        c.rect(8, y - 4, W - 16, 18, stroke=0, fill=1)
    c.setStrokeColorRGB(*colors[r])
    c.setLineWidth(0.8)
    c.setDash(2, 1)
    c.line(10, y + 2, 22, y + 2)
    c.setDash()
    c.setFillColorRGB(0, 0, 0)
    c.setFont('Arial', 6)
    for x, lab in zip(cols, row):
        c.drawString(x, y, lab)
c.setFont('Arial', 5.5)
c.drawString(10, 52, 'Baseline-state comparison at year 1: global P<0.001.')
c.save()
p.merge_page(PdfReader(io.BytesIO(b.getvalue())).pages[0])
save(D / 'Supplementary_Figure_S10_vector.pdf', [p])
a = next((a for a in meta if a['number'] == 10))
a['pages'] = [dict(page=1, width_pt=W, height_pt=H, headers=[dict(label='a.', title='Time to first follow-up SSI signal', label_size=8, title_size=7)], tiles=[], reflowed_risk_and_HR_table=True)]
a['page_count'] = 1
(O / 'S10_verified_risk_and_HR_values.json').write_text(json.dumps(rows, indent=2))
for a in meta:
    path = pathlib.Path(a['pdf'])
    r = PdfReader(path)
    a['page_count'] = len(r.pages)
    for i, pp in enumerate(r.pages):
        a['pages'][i]['page'] = i + 1
        a['pages'][i]['height_pt'] = float(pp.mediabox.height)
    for b in man:
        if b['number'] == a['number']:
            b['pages'] = [dict(panels=', '.join((h['label'].rstrip('.') for h in p['headers']))) for p in a['pages']]
(O / 'cleaned_layout_manifest.json').write_text(json.dumps(meta, indent=2))
(D / 'figure_manifest.json').write_text(json.dumps(man, indent=2))
print('Final compact layouts and complete annotation keys saved.')
