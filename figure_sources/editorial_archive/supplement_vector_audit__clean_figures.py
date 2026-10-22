# Archived editorial source. See docs/FIGURES.md. Path constants adapted; scientific values unchanged.
from _paths import historical_path
import io, json, pathlib, re, math, copy
from collections import Counter
from pypdf import PdfReader, PdfWriter, Transformation
from pypdf.generic import ContentStream, NameObject, DictionaryObject, FloatObject, ArrayObject, TextStringObject, RectangleObject
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
OUT = pathlib.Path(historical_path('workspace/work/supplement_vector_audit'))
CLEAN = OUT / 'cleaned'
CLEAN.mkdir(exist_ok=True)
RAW = CLEAN / 'native'
RAW.mkdir(exist_ok=True)
pdfmetrics.registerFont(TTFont('Arial', historical_path('fonts/Arial.ttf')))
pdfmetrics.registerFont(TTFont('Arial-Bold', historical_path('fonts/Arial Bold.ttf')))
buf = io.BytesIO()
c = canvas.Canvas(buf, pagesize=(500, 500))
for name, y in [('Arial', 200), ('Arial-Bold', 100)]:
    c.setFont(name, 10)
    c.drawString(0, y, ''.join((chr(x) for x in range(32, 127))))
c.save()
fdoc = PdfReader(io.BytesIO(buf.getvalue()))
fd = fdoc.pages[0]['/Resources']['/Font']
REG = [v for v in fd.values() if 'ArialMT' in str(v.get_object().get('/BaseFont'))][0]
BOLD = [v for v in fd.values() if 'Arial-BoldMT' in str(v.get_object().get('/BaseFont'))][0]
records = json.loads((OUT / 'fast_audit.json').read_text())[:20]

def textof(block):
    t = ''
    for a, o in block:
        if o in (b'Tj', b"'", b'"'):
            t += str(a[-1])
        elif o == b'TJ':
            t += ''.join((str(v) for v in a[0] if isinstance(v, (str, TextStringObject))))
    return t.strip()

def blocks(ops):
    i = 0
    while i < len(ops):
        if ops[i][1] == b'BT':
            j = i + 1
            while j < len(ops) and ops[j][1] != b'ET':
                j += 1
            yield (i, j + 1, ops[i:j + 1])
            i = j + 1
        else:
            i += 1

def replacementfont(page):
    fonts = page['/Resources']['/Font']
    for k, v in list(fonts.items()):
        base = str(v.get_object().get('/BaseFont'))
        if 'Helvetica' in base:
            fonts[k] = BOLD if 'Bold' in base else REG

def singlelabel(t):
    return bool(re.fullmatch('[a-jA-J]', t))

def paneltext(t):
    return re.match('^([A-J])\\s{1,2}([A-Z0-9].*)', t)
manifest = []
for rec in records:
    n = int(re.search('(\\d+)', rec['name']).group(1))
    p = PdfReader(rec['source']).pages[0]
    cs = ContentStream(p.get_contents(), p.pdf)
    ops = cs.operations
    removed = [f['text'].strip() for f in rec['pages'][0]['fragments'][-2:]]
    titles = []
    new = []
    i = 0
    for a, b, block in blocks(ops):
        new.extend(ops[i:a])
        t = textof(block)
        if t in removed:
            pass
        else:
            m = paneltext(t)
            if m:
                for args, o in block:
                    if o == b'TJ':
                        for q, v in enumerate(args[0]):
                            if isinstance(v, (str, TextStringObject)):
                                args[0][q] = TextStringObject(str(v).replace(m.group(1) + '  ', m.group(1).lower() + '. ', 1).replace(m.group(1) + ' ', m.group(1).lower() + '. ', 1))
                                break
                    elif o == b'Tj':
                        args[0] = TextStringObject(re.sub('^([A-Z])\\s{1,2}', lambda m: m.group(1).lower() + '. ', str(args[0])))
                titles.append(dict(label=m.group(1).lower() + '.', title=m.group(2)))
            elif singlelabel(t):
                for args, o in block:
                    if o == b'Tj':
                        args[0] = TextStringObject(t.lower() + '.')
                    elif o == b'TJ':
                        args[0] = ArrayObject([TextStringObject(t.lower() + '.')])
                titles.append(dict(label=t.lower() + '.', title=''))
            new.extend(block)
        i = b
    new.extend(ops[i:])
    cs.operations = new
    p[NameObject('/Contents')] = cs
    replacementfont(p)
    w = PdfWriter()
    w.add_page(p)
    dest = RAW / f'Supplementary_Figure_S{n:02d}_native.pdf'
    with dest.open('wb') as f:
        w.write(f)
    manifest.append(dict(number=n, source=rec['source'], native=str(dest), removed_text=removed, panel_titles=titles, source_width=rec['pages'][0]['width'], source_height=rec['pages'][0]['height']))
    print('Native cleaned', n, flush=True)
(OUT / 'cleanup_manifest.json').write_text(json.dumps(manifest, indent=2))
