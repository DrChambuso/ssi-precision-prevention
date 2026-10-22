# Archived editorial source. See docs/FIGURES.md. Path constants adapted; scientific values unchanged.
from _paths import historical_path
import pathlib, json, hashlib
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, TextStringObject, NameObject, FloatObject
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont('Arial', historical_path('fonts/Arial.ttf')))
O = pathlib.Path(historical_path('workspace/work/supplement_vector_audit'))
P = O / 'cleaned/Supplementary_Figure_S01_vector.pdf'
r = PdfReader(P)
p = r.pages[0]
cs = ContentStream(p.get_contents(), r)
ops = cs.operations
replacements = {'Exploratory abdominal': ('Exploratory laparotomy', 257.565, 8), 'Bile duct, liver or': ('Bile duct/liver/pancreas', 243.265, 8), 'Open reduction of': ('Fracture reduction', 228.975, 8), 'Hysterectomy,': ('Abdominal hysterectomy', 157.485, 7.4)}
skip = {'surgery (laparotomy)', 'pancreatic surgery', 'fracture', 'abdominal'}
seen = []
out = []
i = 0
while i < len(ops):
    if ops[i][1] != b'BT':
        out.append(ops[i])
        i += 1
        continue
    j = i + 1
    while ops[j][1] != b'ET':
        j += 1
    block = ops[i:j + 1]
    tm = next((a for a, o in block if o == b'Tm'), None)
    text = ''.join((str(a[-1]) if o == b'Tj' else ''.join((str(v) for v in a[0] if isinstance(v, (str, TextStringObject)))) if o == b'TJ' else '' for a, o in block))
    if tm and float(tm[4]) < 90 and (95 < float(tm[5]) < 266) and (text in skip):
        out.extend(((a, o) for a, o in block if o in (b'cs', b'CS', b'scn', b'SCN', b'rg', b'RG', b'g', b'G')))
        seen.append(text)
    elif tm and float(tm[4]) < 90 and (95 < float(tm[5]) < 266) and (text in replacements):
        new, y, size = replacements[text]
        x = 84 - pdfmetrics.stringWidth(new, 'Arial', size)
        tm[:] = [FloatObject(size), FloatObject(0), FloatObject(0), FloatObject(size), FloatObject(x), FloatObject(y)]
        for a, o in block:
            if o in (b'Tj', b'TJ'):
                out.append(([TextStringObject(new)], b'Tj'))
            else:
                out.append((a, o))
        seen.append(text)
    elif tm and float(tm[4]) < 90 and (95 < float(tm[5]) < 266) and (float(tm[0]) == 8):
        tm[4] = FloatObject(84 - pdfmetrics.stringWidth(text, 'Arial', 8))
        out.extend(block)
    else:
        out.extend(block)
    i = j + 1
assert len(seen) == 8, seen
cs.operations = out
p[NameObject('/Contents')] = cs
w = PdfWriter()
w.add_page(p)
w.pages[0].compress_content_streams()
with P.open('wb') as f:
    w.write(f)
report = {'pdf': str(P), 'sha256': hashlib.sha256(P.read_bytes()).hexdigest(), 'replaced_row_labels': replacements, 'deleted_wrapped_fragments': sorted(skip), 'scientific_values_changed': False, 'row_positions_changed': False}
(O / 'S01_row_label_repair.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
