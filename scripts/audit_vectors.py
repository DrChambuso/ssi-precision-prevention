#!/usr/bin/env python3
"""Audit archived PDF artwork without mistaking PDF containers for pure vectors.

Requires PyMuPDF. Text drawn as glyph outlines remains vector, but cannot be
verified by text extraction. This audit is structural, not visual certification.
"""
from pathlib import Path
import argparse
import collections
import hashlib
import json
import re
import sys

try:
    import pymupdf as fitz
except ImportError:
    raise SystemExit('Install PyMuPDF to run this optional figure audit.')

BAD_DASH = set(chr(v) for v in [0x2010, 0x2011, 0x2012, 0x2013, 0x2014, 0x2015, 0x2212, 0xFE58, 0xFE63, 0xFF0D])

def audit_file(path, root):
    doc = fitz.open(path)
    pages = []
    for index, page in enumerate(doc):
        text = page.get_text()
        text_dict = page.get_text('dict')
        used_fonts = sorted(set(span['font'] for block in text_dict['blocks'] if block['type'] == 0
                                for line in block['lines'] for span in line['spans']))
        fonts = []
        for resource in page.get_fonts(full=True):
            xref, extension, kind, base, name, encoding, *rest = resource
            embedded = False
            if xref:
                try:
                    embedded = bool(doc.extract_font(xref)[3])
                except Exception:
                    pass
            normalized_name = re.sub(r'^[A-Z]{6}\+', '', base)
            fonts.append({'name': base, 'type': kind, 'extension': extension, 'embedded': embedded,
                          'used_in_extractable_text': normalized_name in used_fonts})
        image_info = page.get_image_info(xrefs=True)
        resources = page.get_images(full=True)
        drawings = page.get_cdrawings()
        pages.append({
            'page': index + 1,
            'width_pt': round(page.rect.width, 6),
            'height_pt': round(page.rect.height, 6),
            'displayed_raster_image_occurrences': len(image_info),
            'image_resource_count': len(resources),
            'displayed_image_dimensions_px': sorted(set((r['width'], r['height']) for r in image_info)),
            'vector_drawing_paths': len(drawings),
            'extractable_text_characters': len(text),
            'font_resources': fonts,
            'unembedded_font_resource_count': sum(not f['embedded'] for f in fonts),
            'fonts_used_in_extractable_text': used_fonts,
            'unembedded_fonts_used_in_extractable_text': [f['name'] for f in fonts if not f['embedded'] and f['used_in_extractable_text']],
            'extracted_prohibited_dash_counts': {f'U+{ord(c):04X}': n for c,n in collections.Counter(text).items() if c in BAD_DASH},
            'text_audit_limit': 'Outlined glyph text is not extractable; zero text does not prove missing labels or ASCII-only visible labels.' if len(text.strip()) < 10 else 'Only extractable text audited; outlined glyphs require source inspection.'
        })
    raster = sum(p['displayed_raster_image_occurrences'] for p in pages)
    return {'file': str(path.relative_to(root)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'page_count': len(doc), 'artwork_classification': 'mixed vector and raster' if raster else 'no displayed raster images detected',
            'pages': pages}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    files = sorted((root/'figures').rglob('*.pdf'))
    results = [audit_file(p, root) for p in files]
    mixed = [r['file'] for r in results if r['artwork_classification'] == 'mixed vector and raster']
    dash_files = [r['file'] for r in results if any(p['extracted_prohibited_dash_counts'] for p in r['pages'])]
    output = {'audit_version':'1.0.0', 'pymupdf_version':fitz.VersionBind, 'figure_count':len(results),
              'main_figure_count':sum('/main/' in r['file'] for r in results),
              'supplementary_figure_count':sum('/supplementary/' in r['file'] for r in results),
              'missing_main_figure_numbers_in_source_manuscript':[6,7],
              'mixed_artwork_files':mixed, 'extractable_text_dash_findings':dash_files,
              'scope':'Structural raster/font/text inspection only; no assertion of full numerical reproduction or new clinical validation.',
              'figures':results}
    dest = root/'validation/vector_audit.json';dest.parent.mkdir(exist_ok=True,parents=True)
    dest.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({k:output[k] for k in ['figure_count','main_figure_count','supplementary_figure_count','mixed_artwork_files','extractable_text_dash_findings']},indent=2))
    return 0

if __name__ == '__main__':
    sys.exit(main())
