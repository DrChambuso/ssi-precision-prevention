# Archived editorial source. See docs/FIGURES.md. Path constants adapted; scientific values unchanged.
from _paths import historical_path
from pathlib import Path
from lxml import etree as E
import json, copy, hashlib
root = Path(historical_path('workspace'))
out = root / 'outputs/earlier-profiles-vector'
out.mkdir(exist_ok=True, parents=True)
NS = 'http://www.w3.org/2000/svg'
XL = 'http://www.w3.org/1999/xlink'

def tag(s):
    return '{' + NS + '}' + s
r = E.parse(str(root / 'work/fig10-image16.svg'))
svg = r.getroot()
W, H = (481.889764, 493.228346)
GAP = 36
SPLIT = 289
removed = []
before = [E.tostring(e) for e in svg.iter(tag('path'))]
for e in list(svg.iter(tag('use'))):
    if e.get('y') is None:
        continue
    y = float(e.get('y'))
    if y < 18 or 293 < y < 298:
        removed.append(dict(e.attrib))
        e.getparent().remove(e)
assert len(removed) == 126, len(removed)
assert before == [E.tostring(e) for e in svg.iter(tag('path'))]
defs = svg.find(tag('defs'))
art = E.SubElement(defs, tag('g'), id='preserved-source-artwork')
for e in list(svg):
    if e is not defs:
        svg.remove(e)
        art.append(e)
for name, y, h in [('upper-row-clip', 0, SPLIT), ('lower-row-clip', SPLIT, H - SPLIT)]:
    cp = E.SubElement(defs, tag('clipPath'), id=name, clipPathUnits='userSpaceOnUse')
    E.SubElement(cp, tag('rect'), x='0', y=str(y), width=str(W), height=str(h))
E.SubElement(svg, tag('rect'), x='0', y='0', width=str(W), height=str(H + GAP), fill='white')
for name, offset in [('upper-row-clip', 0), ('lower-row-clip', GAP)]:
    g = E.SubElement(svg, tag('g'), attrib={'clip-path': 'url(#' + name + ')', 'transform': f'translate(0 {offset})'})
    E.SubElement(g, tag('use'), attrib={'{' + XL + '}href': '#preserved-source-artwork'})
headers = [('a.', 'Earlier profiles projected onto later reports', 4.315088, 22.293219, 15), ('b.', 'Later annual SSI signals', 252.926137, 270.904269, 15), ('c.', 'Prior components and operative mix', 4.315088, 22.293219, 295.835825 + GAP), ('d.', 'Later SSI incidence', 252.926137, 270.904269, 295.835825 + GAP)]
spec = []
for letter, title, lx, tx, y in headers:
    for text, x, size in [(letter, lx, 13), (title, tx, 9.5)]:
        spec.append({'text': text, 'x': x, 'y': y, 'font': 'Arial-BoldMT', 'size': size})
(root / 'work/profile-title-spec.json').write_text(json.dumps(spec))
svg.set('width', '843pt')
svg.set('height', f'{(H + GAP) * 843 / W:.6f}pt')
svg.set('viewBox', f'0 0 {W} {H + GAP}')
(root / 'work/profile-layout-base.svg').write_bytes(E.tostring(svg, xml_declaration=True, encoding='UTF-8'))
(root / 'work/profile-layout-manifest.json').write_text(json.dumps({'original_svg': 'Manuscript.docx, word/media/image16.svg', 'new_row_gap_pt_native': GAP, 'additional_gap_pt_output': GAP * 843 / W, 'source_paths_preserved': len(before), 'removed_header_glyph_instances': len(removed), 'headers': headers, 'output_dimensions_pt': [843, (H + GAP) * 843 / W]}, indent=2))
print('Preserved', len(before), 'source paths; removed', len(removed), 'old title glyph instances; prepared new layout.')
