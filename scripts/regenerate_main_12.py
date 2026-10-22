# Final main figure12 renderer. Historical filename14 is retained in internal output names to preserve source lineage.
from pathlib import Path
import csv
import io
import json
from lxml import etree as E
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, NameObject
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import argparse
parser = argparse.ArgumentParser(description='Render final main figure12 from archived numerical tables; no statistical models are refitted.')
parser.add_argument('--font-dir', required=True, help='Directory containing lawfully installed Arial.ttf, Arial Bold.ttf and Arial Italic.ttf')
args = parser.parse_args()
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/derived/main12'
OUT = ROOT / 'generated_figures/main12'
OUT.mkdir(parents=True, exist_ok=True)
WORK = OUT
import shutil
shutil.copyfile(DATA / 'fig14-source-data.json', WORK / 'fig14-source-data.json')
ROWS = json.loads((WORK / 'fig14-source-data.json').read_text())
KEYS = ['procedure', 'cases', 'incidence', 'ratio', 'arr', 'q', 'category']
assert len(ROWS) == 28
assert sum(int(r['cases'].replace(',', '')) for r in ROWS) == 37525

def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

STATS = DATA / 'statistics'
comparisons = read_csv(STATS / 'future_SSI_case_capture_comparisons.csv')
comparison = next(r for r in comparisons if r['comparator'] == 'prior_cases' and float(r['capacity']) == .3)
metrics = read_csv(STATS / 'prediction_metrics_1999_cluster_bootstrap.csv')
auc = next(r for r in metrics if r['dataset'] == 'Test' and r['group'] == 'All ages and procedures' and r['method'] == 'combined' and r['metric'] == 'AUC')
signal = next(r for r in metrics if r['dataset'] == 'Test' and r['group'] == 'All ages and procedures' and r['method'] == 'combined' and r['metric'] == 'capture_30')
national = read_csv(DATA / 'microbiology/national_ssi_source_totals.csv')
national_pathogens = sum(int(r['pathogen_reports']) for r in national)
national_events = sum(int(r['ssi_events']) for r in national)
totals = read_csv(DATA / 'summaries/Age_group_totals.csv')
assert national_pathogens == 378610 and national_events == 330914
assert int(comparison['reports']) == 18132 and int(comparison['SSI_cases']) == 11897
assert int(auc['bootstrap_repeats']) == 1999

MODEL_CAPTURE = float(comparison['combined_capture']) * 100
PRIOR_CAPTURE = float(comparison['comparator_capture']) * 100
GAIN = float(comparison['difference']) * 100
GAIN_LOWER = float(comparison['lower']) * 100
GAIN_UPPER = float(comparison['upper']) * 100
SIGNAL_CAPTURE = float(signal['estimate']) * 100
SIGNAL_LOWER = float(signal['lower']) * 100
SIGNAL_UPPER = float(signal['upper']) * 100
AUC = float(auc['estimate'])
AUC_LOWER = float(auc['lower'])
AUC_UPPER = float(auc['upper'])

FONT_DIR = Path(args.font_dir)
pdfmetrics.registerFont(TTFont('Arial', str(FONT_DIR / 'Arial.ttf')))
pdfmetrics.registerFont(TTFont('ArialBold', str(FONT_DIR / 'Arial Bold.ttf')))
pdfmetrics.registerFont(TTFont('ArialItalic', str(FONT_DIR / 'Arial Italic.ttf')))
W, H = 183 * 72 / 25.4, 481.8
M, INNER = 10, W - 20
NS = 'http://www.w3.org/2000/svg'
svg = E.Element('{' + NS + '}svg', nsmap={None: NS}, width='183mm', height=f'{H * 25.4 / 72:.6f}mm', viewBox=f'0 0 {W} {H}')
E.SubElement(svg, '{' + NS + '}title').text = 'Procedure evidence, capacity-dependent prediction gains and microbiology-informed local review'
E.SubElement(svg, '{' + NS + '}desc').text = 'Complete 28-procedure evidence table, paired SSI case and annual signal capture gains at three review capacities with 95 percent confidence intervals, and independent national pathogen enrichment examples informing local review. All text and artwork remain editable vectors.'
E.SubElement(svg, '{' + NS + '}rect', x='0', y='0', width=str(W), height=str(H), fill='#FFFFFF')
svg_group = svg
buffer = io.BytesIO()
c = canvas.Canvas(buffer, pagesize=(W, H))
fonts_used, text_audit, marks = [], [], []

def group(name):
    global svg_group
    svg_group = E.SubElement(svg, '{' + NS + '}g', id=name)

def rgb(value):
    return tuple(int(value[i:i + 2], 16) / 255 for i in (1, 3, 5))

def text(value, x, y, size=5.8, bold=False, anchor='start', color='#111111', role=None, italic=False):
    font = 'ArialItalic' if italic else 'ArialBold' if bold else 'Arial'
    width = pdfmetrics.stringWidth(value, font, size)
    xx = x - width / 2 if anchor == 'middle' else x - width if anchor == 'end' else x
    c.setFont(font, size)
    c.setFillColorRGB(*rgb(color))
    c.drawString(xx, y, value)
    el = E.SubElement(svg_group, '{' + NS + '}text', x=f'{x:.4f}', y=f'{H-y:.4f}', fill=color,
                      attrib={'font-family': 'Arial, Helvetica, sans-serif', 'font-size': str(size),
                              'font-weight': '700' if bold else '400', 'font-style': 'italic' if italic else 'normal', 'text-anchor': anchor})
    el.text = value
    fonts_used.append(size)
    text_audit.append({'text': value, 'x': xx, 'y': y, 'size': size, 'width': width, 'bold': bold, 'italic': italic, 'role': role, 'group': svg_group.get('id')})
    assert xx >= M - .5 and xx + width <= W - M + .5, (value, xx, width)

def rect(x, y, w, h, fill=None, stroke=None, lw=.35, role=None):
    if fill:
        c.setFillColorRGB(*rgb(fill))
    if stroke:
        c.setStrokeColorRGB(*rgb(stroke))
    c.setLineWidth(lw)
    c.rect(x, y, w, h, fill=bool(fill), stroke=bool(stroke))
    E.SubElement(svg_group, '{' + NS + '}rect', x=f'{x:.4f}', y=f'{H-y-h:.4f}', width=f'{w:.4f}', height=f'{h:.4f}',
                 fill=fill or 'none', stroke=stroke or 'none', attrib={'stroke-width': str(lw)})
    if role:
        marks.append({'role': role, 'x': x, 'y': y, 'width': w, 'height': h})

def line(x1, y1, x2, y2, color='#6D7780', lw=.4):
    c.setStrokeColorRGB(*rgb(color))
    c.setLineWidth(lw)
    c.line(x1, y1, x2, y2)
    E.SubElement(svg_group, '{' + NS + '}line', x1=f'{x1:.4f}', y1=f'{H-y1:.4f}', x2=f'{x2:.4f}', y2=f'{H-y2:.4f}',
                 stroke=color, attrib={'stroke-width': str(lw)})

def path(points, color='#6D7780', lw=.5, arrow=False):
    p = c.beginPath()
    p.moveTo(*points[0])
    for xx, yy in points[1:]:
        p.lineTo(xx, yy)
    c.setStrokeColorRGB(*rgb(color))
    c.setLineWidth(lw)
    c.drawPath(p, stroke=1, fill=0)
    d = 'M ' + ' L '.join(f'{xx:.4f} {H-yy:.4f}' for xx, yy in points)
    E.SubElement(svg_group, '{' + NS + '}path', d=d, fill='none', stroke=color, attrib={'stroke-width': str(lw)})
    if arrow:
        x1, y1 = points[-2]
        xx, yy = points[-1]
        if xx == x1:
            dy = 2.1 if yy < y1 else -2.1
            path([(xx-1.5, yy+dy), (xx, yy), (xx+1.5, yy+dy)], color, lw)
        else:
            dx = -2.1 if xx > x1 else 2.1
            path([(xx+dx, yy-1.5), (xx, yy), (xx+dx, yy+1.5)], color, lw)

def panel(letter, title, x, y):
    text(letter + '.', x, y, 8, True, role='panel-label')
    text(title, x+13, y, 7, True, role='panel-title')

group('a-complete-procedure-evidence')
panel('a', 'Procedure evidence for prevention and stewardship review', M, 469.8)
widths = [126, 50, 50, 50, 100, 50, INNER-426]
starts = [M]
for width in widths:
    starts.append(starts[-1]+width)
centers = [(starts[i]+starts[i+1])/2 for i in range(7)]
headers = [['Procedure'], ['SSI cases'], ['SSIs per', '1,000 operations'], ['Observed /', 'predicted'],
           ['Next-year signal aRR', '(95% CI)'], ['BH q'], ['National SSI', 'category']]
for i, labels in enumerate(headers):
    for j, label in enumerate(labels):
        text(label, starts[i]+3 if i == 0 else centers[i], 451.8-j*7.4, 5.6, True, 'start' if i == 0 else 'middle', role='column-header')
TOP, RH = 438.8, 8.3
line(M, TOP, W-M, TOP, '#75818A', .45)
for i, row in enumerate(ROWS):
    bottom = TOP-(i+1)*RH
    baseline = bottom+2.15
    if i % 2 == 0:
        rect(M, bottom, INNER, RH, fill='#F3F5F6')
    for j, key in enumerate(KEYS):
        value = row[key].lstrip('=') if key == 'q' else row[key]
        text(value, starts[j]+3 if j == 0 else centers[j], baseline, 5.8, True,
             'start' if j == 0 else 'middle', role=f'table-{i}-{key}')
line(M, TOP-28*RH, W-M, TOP-28*RH, '#75818A', .45)

def dot(x, y, r=1.8, fill='#0072B2', stroke=None, square=False, role=None):
    if square:
        rect(x-r, y-r, 2*r, 2*r, fill=fill, stroke=stroke, lw=.55)
    else:
        c.setLineWidth(.55)
        if fill:
            c.setFillColorRGB(*rgb(fill))
        if stroke:
            c.setStrokeColorRGB(*rgb(stroke))
        c.circle(x, y, r, fill=bool(fill), stroke=bool(stroke))
        E.SubElement(svg_group, '{'+NS+'}circle', cx=f'{x:.4f}', cy=f'{H-y:.4f}', r=str(r),
                     fill=fill or 'none', stroke=stroke or 'none', attrib={'stroke-width': '.55'})
    if role:
        marks.append({'role': role, 'x': x, 'y': y, 'radius': r, 'square': square})

def interval(x, lower, upper, color, horizontal=False):
    if horizontal:
        line(lower, x, upper, x, color, .7)
        line(lower, x-1.5, lower, x+1.5, color, .6)
        line(upper, x-1.5, upper, x+1.5, color, .6)
    else:
        line(x, lower, x, upper, color, .75)
        line(x-1.5, lower, x+1.5, lower, color, .6)
        line(x-1.5, upper, x+1.5, upper, color, .6)

paired = read_csv(STATS / 'prediction_paired_comparisons_1999_cluster_bootstrap.csv')
case_rows = sorted([r for r in comparisons if r['comparator'] == 'prior_cases'], key=lambda r: float(r['capacity']))
signal_rows = [next(r for r in paired if r['dataset'] == 'Test' and r['group'] == 'All ages and procedures'
                   and r['comparator'] == 'prior_cases' and r['metric'] == 'capture_'+str(cap)) for cap in [10, 20, 30]]
assert len(case_rows) == 3
gain_rows = []
for cr, sr in zip(case_rows, signal_rows):
    assert int(cr['reports']) == int(sr['reports']) == 18132
    assert int(cr['sites']) == int(sr['sites']) == 337
    assert int(cr['bootstrap_repeats']) == int(sr['bootstrap_repeats']) == 1999
    for outcome, row in [('cases', cr), ('signals', sr)]:
        gain_rows.append({'capacity': int(round(float(cr['capacity'])*100)), 'outcome': outcome,
                          'estimate': float(row['difference'])*100, 'lower': float(row['lower'])*100,
                          'upper': float(row['upper'])*100})

group('b-capacity-dependent-capture-gains')
BX, BW = M, (INNER-20)/2
CX, CW = BX+BW+20, BW
panel('b', 'Capture gains depend on review capacity', BX, 176)
BLUE, GOLD = '#0072B2', '#A86C12'
dot(BX+3, 155.8, 1.7, BLUE)
text('SSI case capture', BX+9, 154, 5.5, True)
dot(BX+94, 155.8, 1.7, GOLD, square=True)
text('Annual signal capture', BX+100, 154, 5.5, True)
text('Gain vs prior counts (percentage points; 95% CI)', BX, 143, 5.4, True)
XP0, XP1, YP0, YP1 = BX+38, BX+205, 48, 133
def gain_y(value):
    return YP0+(value+10)/20*(YP1-YP0)
line(XP0, YP0, XP0, YP1, '#4B555D', .5)
line(XP0, YP0, XP1, YP0, '#4B555D', .5)
for tick in [-10, -5, 0, 5, 10]:
    yy = gain_y(tick)
    line(XP0-2.5, yy, XP0, yy, '#4B555D', .45)
    text(str(tick), XP0-5.5, yy-1.7, 5.3, anchor='end')
line(XP0, gain_y(0), XP1, gain_y(0), '#7E878E', .75)
x_centers = {10: BX+62, 20: BX+123, 30: BX+184}
for cap, xx in x_centers.items():
    line(xx, YP0, xx, YP0-2.5, '#4B555D', .45)
    text(str(cap), xx, 38, 5.5, True, 'middle')
for record in gain_rows:
    case = record['outcome'] == 'cases'
    xx = x_centers[record['capacity']]+(-4 if case else 4)
    color = BLUE if case else GOLD
    interval(xx, gain_y(record['lower']), gain_y(record['upper']), color)
    dot(xx, gain_y(record['estimate']), 1.9, color, square=not case,
        role=f'paired-{record["outcome"]}-{record["capacity"]}')
    label_y = gain_y(record['estimate'])-(8.1 if case and abs(record['estimate']) < 1 else 1.6)
    text(f'{record["estimate"]:+.2f}', xx+(-4 if case else 4), label_y,
         5.4, True, 'end' if case else 'start', role=f'gain-label-{record["outcome"]}-{record["capacity"]}')
text('Report-review capacity (%)', (XP0+XP1)/2, 27, 5.8, True, 'middle')

group('c-microbiology-informed-review')
panel('c', 'Replicated pathogen patterns and local review', CX, 176)
enrichment = read_csv(DATA / 'microbiology/pooled_category_enrichment_tests.csv')
replication = read_csv(DATA / 'microbiology/cross_period_pathogen_signal_replication.csv')
selected = []
for category, organism in [('Orthopedic', 'Staphylococcus aureus'), ('Abdominal', 'Escherichia coli')]:
    row = next(r for r in enrichment if r['age_group'] == 'adult' and r['surgical_category'] == category and r['organism'] == organism)
    repeated = next(r for r in replication if r['age_group'] == 'adult' and r['surgical_category'] == category and r['organism'] == organism)
    assert repeated['same_direction'] == repeated['both_BH_q_below_005'] == repeated['taxonomy_stable'] == 'True'
    assert int(row['total1'])+int(row['total0']) == 369802
    selected.append(row)
dot(CX+3, 155.8, 1.7, BLUE)
text('Within category', CX+9, 154, 5.3, True)
dot(CX+99, 155.8, 1.7, fill='#FFFFFF', stroke='#6D7780')
text('Other categories', CX+105, 154, 5.3, True)
text('Share ratio (95% CI)', CX+187, 142, 5.1, True, 'middle')
MP0, MPW = CX+8, 122
def share_x(value):
    return MP0+value/40*MPW
for i, row in enumerate(selected):
    yy = 124 if i == 0 else 75
    header_y = 140 if i == 0 else 91
    category = row['surgical_category']
    label = 'S. aureus' if i == 0 else 'E. coli'
    text(category, CX, header_y, 6.1, True)
    species_x = CX+pdfmetrics.stringWidth(category, 'ArialBold', 6.1)+5
    text('|', species_x, header_y, 6.1)
    text(label, species_x+6, header_y, 6.1, italic=True)
    p1, p0 = float(row['share1'])*100, float(row['share0'])*100
    line(share_x(p0), yy, share_x(p1), yy, '#A8B3BA', .9)
    interval(yy, share_x(float(row['share0_lower'])*100), share_x(float(row['share0_upper'])*100), '#6D7780', True)
    interval(yy, share_x(float(row['share1_lower'])*100), share_x(float(row['share1_upper'])*100), BLUE, True)
    dot(share_x(p0), yy, 1.9, fill='#FFFFFF', stroke='#6D7780', role=f'{category}-share-other')
    dot(share_x(p1), yy, 1.9, BLUE, role=f'{category}-share-within')
    text(f'{p0:.1f}%', share_x(p0), yy+5, 5.4, anchor='middle')
    text(f'{p1:.1f}%', share_x(p1), yy+5, 5.4, True, 'middle')
    text(f'{float(row["report_share_ratio"]):.2f}', CX+187, yy+1.5, 6.7, True, 'middle')
    text(f'({float(row["ratio_lower"]):.2f}-{float(row["ratio_upper"]):.2f})', CX+187, yy-7.3, 5.4, anchor='middle')
    if i == 0:
        line(CX, 100, CX+CW, 100, '#D5DCE1', .4)
line(MP0, 61, MP0+MPW, 61, '#4B555D', .5)
for tick in [0, 10, 20, 30, 40]:
    xx = share_x(tick)
    line(xx, 61, xx, 58.5, '#4B555D', .45)
    text(str(tick), xx, 51, 5.2, anchor='middle')
text('Pathogen-report share (%)', MP0+MPW/2, 40.5, 5.5, True, 'middle')

c.save()
buffer.seek(0)
reader = PdfReader(buffer)
page = reader.pages[0]
content = ContentStream(page.get_contents(), reader)
font_resources = page['/Resources']['/Font']
unused = [key for key, f in font_resources.items() if f.get_object().get('/BaseFont') == '/Helvetica']
content.operations = [(args, operator) for args, operator in content.operations if not (operator == b'Tf' and args[0] in unused)]
for key in unused:
    del font_resources[key]
page[NameObject('/Contents')] = content
writer = PdfWriter()
writer.add_page(page)
writer.add_metadata({'/Title': 'Figure 14 - procedure evidence, capacity-dependent capture and microbiology-informed review',
                     '/Subject': 'Editable vector figure retaining 28-procedure evidence and presenting paired capture gains and separate national pathogen enrichment.'})
pdf_path = OUT / 'Fig_14_bold_panel_a_vector.pdf'
with pdf_path.open('wb') as f:
    writer.write(f)
svg_path = OUT / 'Fig_14_bold_panel_a_vector.svg'
svg_path.write_bytes(E.tostring(svg, encoding='UTF-8', xml_declaration=True, pretty_print=True))

legend = '''Figure 14. Procedure evidence, capacity-dependent prioritization and microbiology-informed local review.

a, Hospital surveillance comprised 72,854 annual reports, 6,737,972 operations and 37,525 surgical site infections across 28 procedures during 2016-2025. All 28 procedures are ordered by reported SSI burden, with reported surgical site infection (SSI) counts, incidence per 1,000 operations, pooled observed-to-predicted ratios, adjusted next-year signal risk ratios (aRRs), 95% confidence intervals (CIs), Benjamini-Hochberg (BH) q values and national SSI microbiology categories. A signal is an annual observed SSI count above the source-predicted count. The aRR compares next-year signal frequency after an above-predicted versus at-or-below-predicted annual report. Inference accounts for hospital clustering, with BH correction for 28 planned procedure tests. NE denotes an unavailable estimate. National categories provide separate context; neither kidney category has a dedicated pathogen profile in the available source tables.

b, Paired differences in future SSI case capture (circles) and future annual signal capture (squares), comparing the history-informed model with ranking by prior SSI counts at 10%, 20% and 30% report-review capacity. Positive values favor the model; negative values favor prior counts. Points are estimates and whiskers are 95% CIs from 1,999 paired whole-hospital bootstrap resamples. The test set comprised 18,132 reports from 337 hospitals during 2023-2025, with 11,897 SSIs and 3,540 annual signals. A model trained on 2017-2022 targets was frozen before testing. Case-capture gains at the three capacities were -5.85 (95% CI -7.75 to -3.93), +0.05 (-1.36 to 1.75) and +3.71 (1.52 to 5.86) percentage points. Corresponding signal-capture gains were +0.89 (-0.20 to 1.74), +2.39 (1.37 to 3.54) and +6.11 (3.79 to 8.32) points. At 30% capacity, the model captured 81.0% of future reported SSIs and 62.7% of future annual signals. The case and signal percentages have different denominators. Only the three tested capacities are shown; no exact crossover threshold is inferred. Capture measures retrospective prioritization and does not measure infections prevented.

c, Two replicated national adult pathogen-report enrichment findings, pooled across the nonoverlapping 2015-2017 and 2018-2021 periods (369,802 pathogen reports across surgical categories). Filled circles indicate the selected pathogen's share within the specified category; open circles indicate its share across all other surgical categories. Small whiskers show Wilson 95% proportion CIs. Orthopedic Staphylococcus aureus represented 32,712/91,760 reports (35.6%), compared with 27,459/278,042 (9.9%) elsewhere, a report-share ratio of 3.61 (95% CI 3.56-3.66). Abdominal Escherichia coli represented 38,628/195,582 reports (19.8%), compared with 12,992/174,220 (7.5%) elsewhere, a ratio of 2.65 (2.60-2.70). Ratio CIs use the log-ratio method. Both contrasts had pooled BH q<0.001 and repeated in direction and significance in each source period. These report-share ratios describe pathogen composition, rather than patient-level infection or resistance risk. The national summaries are not linked to California hospitals, patients, SSI events or isolates. The orthopedic finding prompts local review of skin and implant prevention and local S. aureus and MRSA findings. The abdominal finding prompts review of deep/organ-space specimen collection, source-control assessment and local susceptibility before prophylaxis changes. These proposed local questions are supported by the separate microbiology context and procedure-category crosswalk. Local cultures and antimicrobial susceptibility testing (AST), prevention processes and guideline-concordant prophylaxis require review before any regimen change; clinical benefits require prospective evaluation.

MRSA, methicillin-resistant Staphylococcus aureus; Ob/Gyn, obstetric and gynecologic procedures.
'''
legend_path = OUT / 'Fig_14_bold_panel_a_legend.txt'
legend_path.write_text(legend)
new_reader = PdfReader(pdf_path)
pdf_text = new_reader.pages[0].extract_text()
bad_chars = '\u2010\u2011\u2012\u2013\u2014\u2015\u2212\ufe58\ufe63\uff0d'
assert not any(ch in pdf_text+svg_path.read_text()+legend for ch in bad_chars)
assert all(5 <= size <= 7 or size == 8 for size in fonts_used)
assert sum(size == 8 for size in fonts_used) == 3
assert H <= 170*72/25.4
assert len(new_reader.pages[0].images) == 0
assert len(svg.findall('.//{'+NS+'}image')) == 0
report = {'pdf': str(pdf_path.relative_to(ROOT)), 'svg': str(svg_path.relative_to(ROOT)), 'legend': str(legend_path.relative_to(ROOT)), 'dimensions_mm': [183, H*25.4/72],
          'rows': 28, 'source_cells': 196, 'ssi_case_total': 37525, 'pdf_images': 0, 'svg_images': 0,
          'body_font_range_pt': [min(fonts_used), 7], 'panel_labels_pt': 8, 'ascii_dash_audit': 'passed',
          'gain_rows': gain_rows, 'pathogen_source_rows': selected, 'marks': marks}
(WORK / 'fig14-bold-panel-a-verification.json').write_text(json.dumps(report, indent=2))
(WORK / 'fig14-bold-panel-a-text-bounds.json').write_text(json.dumps(text_audit, indent=2))
print(json.dumps({k: report[k] for k in ['pdf', 'svg', 'legend', 'dimensions_mm', 'rows', 'pdf_images', 'svg_images', 'gain_rows']}, indent=2))

