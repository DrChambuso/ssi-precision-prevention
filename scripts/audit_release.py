#!/usr/bin/env python3
"""Check release checksums and portable text without modifying study artifacts."""
from pathlib import Path
import argparse,gzip,hashlib,json,re,sys
EXCLUDE={'results','generated_figures','__pycache__','.git','.venv'}
TEXT={'.md','.txt','.json','.csv','.py','.R','.cff','.yaml','.yml','.toml','.sh','.tsv','.log','.svg'}
BAD=set(range(0x2010,0x2016))|{0x2212,0xad,0xfe58,0xfe63,0xff0d}
BAD_RE=re.compile('['+''.join(chr(x) for x in sorted(BAD))+']')
def files(root):
    return sorted(p for p in root.rglob('*') if p.is_file() and not any(x in EXCLUDE for x in p.relative_to(root).parts) and p.suffix not in {'.pyc','.zip'} and p.name!='.DS_Store')
def audit(root,write=False):
    root=Path(root); manifest=root/'manifest.sha256'; entries=files(root);issues=[]
    for p in entries:
        if p.suffix not in TEXT and not p.name.endswith('.csv.gz'):continue
        try:s=gzip.decompress(p.read_bytes()).decode('utf-8-sig') if p.name.endswith('.csv.gz') else p.read_text(encoding='utf-8-sig')
        except UnicodeDecodeError:issues.append({'file':str(p.relative_to(root)),'issue':'non-UTF8 release text'});continue
        bad=sorted(set(ord(c) for c in BAD_RE.findall(s)))
        if bad:issues.append({'file':str(p.relative_to(root)),'issue':'prohibited dash/minus','codepoints':bad})
        if re.search(r'/' + r'Users/[^/\s]+/',s) or ('/var/'+'folders/') in s:issues.append({'file':str(p.relative_to(root)),'issue':'absolute author-computer path'})
    covered=[p for p in entries if p!=manifest]
    if write:
        manifest.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(root).as_posix()+'\n' for p in covered))
    else:
        expected={line[66:]:line[:64] for line in manifest.read_text().splitlines()}
        current={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in covered}
        for name,digest in expected.items():
            if current.get(name)!=digest:issues.append({'file':name,'issue':'missing file or checksum mismatch'})
        for name in current.keys()-expected.keys():issues.append({'file':name,'issue':'unmanifested file'})
    result={'status':'pass' if not issues else 'fail','files_checked':len(covered),'issues':issues,'excluded_runtime_directories':sorted(EXCLUDE),'scope':'UTF8 text, ASCII dash policy, author-computer path scan and SHA256 file integrity; PDF drawing content is audited separately'}
    print(json.dumps(result,indent=2));return result
if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);a.add_argument('--write-manifest',action='store_true');v=a.parse_args();r=audit(v.root,v.write_manifest);sys.exit(0 if r['status']=='pass' else 1)
