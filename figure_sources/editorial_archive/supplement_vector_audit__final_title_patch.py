# Archived editorial source. See docs/FIGURES.md. Path constants adapted; scientific values unchanged.
from _paths import historical_path
import json, pathlib
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, TextStringObject, NameObject, FloatObject
O = pathlib.Path(historical_path('workspace/work/supplement_vector_audit'))
D = O / 'cleaned'
changes = {16: ('Microbiology evidence gaps', 'Change in missing-pathogen reporting'), 17: ('Procedure-specific review questions', 'Orthopedic S. aureus enrichment')}
for n, (old, new) in changes.items():
    path = D / f'Supplementary_Figure_S{n:02d}_vector.pdf'
    r = PdfReader(path)
    p = r.pages[-1]
    cs = ContentStream(p.get_contents(), r)
    ops = []
    count = 0
    current_font = None
    if n == 17:
        italic = next((v for v in r.pages[0]['/Resources']['/Font'].values() if 'Arial-BoldItalicMT' in str(v.get_object().get('/BaseFont', ''))))
        p['/Resources']['/Font'][NameObject('/FinalBoldItalic')] = italic
    for args, op in cs.operations:
        if op == b'Tf':
            current_font = args[0]
        if op == b'Tj' and str(args[0]) == old:
            count += 1
            if n == 16:
                ops.append(([TextStringObject(new)], b'Tj'))
            else:
                ops.extend([([TextStringObject('Orthopedic ')], b'Tj'), ([NameObject('/FinalBoldItalic'), FloatObject(7)], b'Tf'), ([TextStringObject('S. aureus')], b'Tj'), ([current_font, FloatObject(7)], b'Tf'), ([TextStringObject(' enrichment')], b'Tj')])
        else:
            ops.append((args, op))
    assert count == 1, (n, count)
    cs.operations = ops
    p[NameObject('/Contents')] = cs
    w = PdfWriter()
    for page in r.pages:
        w.add_page(page)
        w.pages[-1].compress_content_streams()
    with open(path, 'wb') as f:
        w.write(f)
meta = json.loads((O / 'cleaned_layout_manifest.json').read_text())

def walk(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str):
                for old, new in changes.values():
                    v = v.replace(old, new)
                obj[k] = v
            else:
                walk(v)
    elif isinstance(obj, list):
        for v in obj:
            walk(v)
walk(meta)
(O / 'cleaned_layout_manifest.json').write_text(json.dumps(meta, indent=2))
print('Updated final S16d and S17d titles without altering panel geometry or data.')
