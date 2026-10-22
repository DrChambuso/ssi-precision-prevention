# Archived editorial source. See docs/FIGURES.md. Path constants adapted; scientific values unchanged.
from _paths import historical_path
from pathlib import Path
import json, math, re
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, Color
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, ContentStream
O = Path('work/supplement_inventory/cleaned')
OUT = O / 'Figure_S21.pdf'
pdfmetrics.registerFont(TTFont('Arial', historical_path('fonts/Arial.ttf')))
pdfmetrics.registerFont(TTFont('ArialBold', historical_path('fonts/Arial Bold.ttf')))
W = 183 * 72 / 25.4
H = 335
c = canvas.Canvas(str(OUT), pagesize=(W, H))
c.setTitle('Supplementary Figure 21. Implementation framework and convergence of prevention-review evidence')
c.setAuthor('')
c.setSubject('Proposed framework; source data and metadata in accompanying legend')
ink = '#111111'
lineink = '#253F4D'
blue = '#BED8E3'
purple = '#CBC3DA'
green = '#D8E3D5'
gray = '#D8DEE1'
yellow = '#F3E8BF'
audit = []

def text(t, x, y, size=6, bold=True, anchor='start'):
    assert not re.search('[\u2010-\u2015\u2212]', t), repr(t)
    font = 'ArialBold' if bold else 'Arial'
    c.setFont(font, size)
    c.setFillColor(HexColor(ink))
    width = pdfmetrics.stringWidth(t, font, size)
    if anchor == 'middle':
        x -= width / 2
    if anchor == 'end':
        x -= width
    c.drawString(x, y, t)
    audit.append({'text': t, 'x': x, 'y': y, 'width': width, 'size': size, 'bold': bold})

def lines(ts, x, y, size=6, leading=7, bold=True, anchor='middle'):
    for i, t in enumerate(ts):
        text(t, x, y - i * leading, size, bold, anchor)

def panel(lab, title, x, y=322):
    text(lab, x, y, 8, True)
    text(title, x + 13, y, 7, True)

def arrow(x1, y1, x2, y2):
    c.setStrokeColor(HexColor(lineink))
    c.setFillColor(HexColor(lineink))
    c.setLineWidth(0.65)
    c.line(x1, y1, x2, y2)
    p = c.beginPath()
    p.moveTo(x2, y2)
    p.lineTo(x2 - 2.4, y2 + 1.7)
    p.lineTo(x2 - 2.4, y2 - 1.7)
    p.close()
    c.drawPath(p, stroke=0, fill=1)
panel('a.', 'Action framework', 10)
cx = 127
cy = 222
r = 75
ir = 51
for angle, color in [(45, gray), (135, purple), (225, green), (315, yellow)]:
    c.setFillColor(HexColor(color))
    c.setStrokeColor(HexColor('#FFFFFF'))
    c.setLineWidth(1.4)
    c.wedge(cx - r, cy - r, cx + r, cy + r, startAng=angle, extent=90, stroke=1, fill=1)
c.setFillColor(HexColor('#FFFFFF'))
c.circle(cx, cy, ir, stroke=0, fill=1)
c.setFillColor(HexColor(yellow))
c.setStrokeColor(HexColor(lineink))
c.setLineWidth(0.65)
c.circle(cx, cy, 31, stroke=1, fill=1)
lines(['SSI prevention', 'review'], cx, 225, 6.4, 8)
lines(['Evidence and', 'policy'], cx, 286, 5.8, 6.7)
lines(['Clinical', 'integration'], cx + 64, 225, 5.8, 6.7)
lines(['Implementation', 'review'], cx, 160, 5.8, 6.7)
lines(['Monitoring', 'and feedback'], cx - 64, 225, 5.8, 6.7)
text('Reliable reports', cx, 263, 5.7, True, 'middle')
text('Priority', cx + 39, 242, 5.7, True, 'middle')
text('Procedure audits', cx, 179, 5.7, True, 'middle')
text('Feedback', cx - 41, 204, 5.7, True, 'middle')
panel('b.', 'Four-stage implementation progression', 10, 122)
cardw = 52
gap = 7
xs = [10 + i * (cardw + gap) for i in range(4)]
carddata = [(['1. Detect'], ['Annual counts', 'and operation', 'denominators'], blue), (['2. Retain', 'history'], ['Earlier signals', 'and quiet', 'reports'], purple), (['3. Target', 'review'], ['Service audit', 'and local', 'AST review'], '#D6CBE2'), (['4. Evaluate'], ['Review uptake,', 'calibration and', 'later SSI rates'], gray)]
for i, (head, body, color) in enumerate(carddata):
    x = xs[i]
    c.setFillColor(HexColor(color))
    c.setStrokeColor(HexColor(lineink))
    c.setLineWidth(0.6)
    c.roundRect(x, 30, cardw, 76, 2, stroke=1, fill=1)
    lines(head, x + cardw / 2, 94, 6.2, 7.1)
    lines(body, x + cardw / 2, 65, 5.6, 7.4, bold=False)
    if i < 3:
        arrow(x + cardw + 1.1, 68, x + cardw + gap - 1, 68)
panel('c.', 'Convergence of review evidence', 269)
c.setLineWidth(0.7)
for x, y, col in [(354, 232, blue), (436, 232, purple), (395, 162, gray)]:
    c.saveState()
    c.setFillAlpha(0.6)
    c.setFillColor(HexColor(col))
    c.setStrokeColor(HexColor(lineink))
    c.circle(x, y, 70, stroke=1, fill=1)
    c.restoreState()
lines(['SSI burden', 'California surveillance'], 341, 268, 6.2, 9)
lines(['Future signals', 'Frozen report model'], 449, 268, 6.2, 9)
lines(['Review', 'priority'], 395, 222, 6.5, 8)
lines(['Procedure-focused', 'prevention', 'questions'], 354, 185, 5.8, 7.5)
lines(['Local culture,', 'AST and', 'prescribing review'], 436, 185, 5.8, 7.5)
lines(['Microbiology context', 'Separate national source'], 395, 125, 6.2, 9)
c.showPage()
c.save()
r = PdfReader(OUT)
w = PdfWriter()
w.append(r)
for p in w.pages:
    cs = ContentStream(p.get_contents(), w)
    cs.operations = [(args, op) for args, op in cs.operations if not (op == b'Tf' and str(args[0]) == '/F1')]
    p[NameObject('/Contents')] = w._add_object(cs)
    fonts = p['/Resources'].get('/Font', {}).get_object()
    for k in list(fonts):
        f = fonts[k].get_object()
        if str(f.get('/BaseFont', '')) == '/Helvetica':
            del fonts[k]
w.add_metadata({'/Title': 'Supplementary Figure 21. Implementation framework and convergence of prevention-review evidence', '/Author': '', '/Subject': 'Proposed prevention-review framework'})
with OUT.open('wb') as f:
    w.write(f)
source = Path(historical_path('project/Figures_MAINTEXT/Fig 16.pdf'))
legend = 'Supplementary Figure 21. Implementation framework and convergence of prevention-review evidence. a, Proposed framework linking reliable source reports, clinical integration, implementation review and feedback. b, Four implementation stages: validate counts and operation denominators; retain earlier signals and quiet reports; target service and local antimicrobial susceptibility testing (AST) review; and evaluate review uptake, calibration and subsequent SSI incidence. The surveillance foundation comprised 72,854 annual California reports, 6,737,972 operations and 37,525 SSIs during 2016-2025. An earlier above-predicted report followed by one quiet report remained associated with a subsequent signal relative to two quiet reports (adjusted risk ratio 1.57, 95% CI 1.48-1.67). In 18,132 held-out reports from 2023-2025, the frozen model achieved an AUC of 0.781 (95% CI 0.771-0.792). At 30% review capacity it captured 62.7% of future annual signals and 81.0% of future SSI cases, with a 3.71-percentage-point gain in case capture over prior SSI counts (95% CI 1.52-5.86; P=0.001). c, Conceptual convergence of reported SSI burden, future signal prediction and separate national microbiology context. National reports comprised 378,610 pathogen reports from 330,914 SSI events in 2015-2017 and 2018-2021. Circle areas and overlaps are illustrative and do not represent patient overlap, linked records or measured intersections. National microbiology is not linked to California hospitals, patients or isolates. A signal is an annual observed SSI count above the source-predicted count; quiet means at or below prediction. The history and capture estimates use hospital-level uncertainty. Report patterns identify review priorities; local cultures, susceptibility, prevention-process and prescribing information inform subsequent action. Clinical benefit and implementation outcomes require prospective evaluation. AST, antimicrobial susceptibility testing; AUC, area under the receiver operating characteristic curve; CI, confidence interval; SSI, surgical site infection.'
removed = ['Overall title: Turning surgical surveillance evidence into prevention-review priorities', 'Four outer explanatory action paragraphs moved to legend', 'All numerical/cohort/capture metadata in b and c moved to legend', 'Decorative bar glyphs inside convergence circles removed; they were schematic and encoded no independent dataset', 'Cohort anchors and implementation test callout box removed; numeric results retained in legend', 'Report patterns select review priority; clinical review determines action.', 'Proposed review framework and prospective-evaluation footer moved to legend', 'Source definition and abbreviations footer moved to legend']
(O / 'removed_annotations.txt').write_text('\n'.join(removed) + '\n')
(O / 'Figure_S21_legend.txt').write_text(legend + '\n')
meta = {'figure_number': 21, 'source': str(source), 'title': 'Implementation framework and convergence of prevention-review evidence', 'legend': legend, 'panels': {'a': 'Action framework', 'b': 'Four-stage implementation progression', 'c': 'Convergence of review evidence'}, 'physical_width_mm': 183, 'physical_height_mm': H * 25.4 / 72, 'all_numerical_results_moved_to_legend': True, 'circle_overlap_is_conceptual': True, 'removed_annotations': removed}
(O / 'Figure_S21_legend_title.json').write_text(json.dumps(meta, indent=2))
(O / 'Figure_S21_text_geometry.json').write_text(json.dumps(audit, indent=2))
r = PdfReader(OUT)
t = ''.join((p.extract_text() or '' for p in r.pages))
assert not re.search('[\u2010-\u2015\u2212]', t)
assert not re.search('[\u2010-\u2015\u2212]', legend)
assert all((0 <= a['x'] and a['x'] + a['width'] <= W for a in audit))
print(OUT.resolve())
print('Text elements', len(audit), 'Page', W, H)
