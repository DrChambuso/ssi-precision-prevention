#!/usr/bin/env python3
"""Download the 22 exact public source resources, rejecting any changed snapshot."""
from pathlib import Path
import argparse,csv,hashlib,urllib.request

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination',type=Path,required=True)
    args=parser.parse_args();args.destination.mkdir(parents=True,exist_ok=True)
    root=Path(__file__).resolve().parents[1]
    for row in csv.DictReader((root/'provenance/california_source_manifest.csv').open()):
        target=args.destination/row['filename']
        if target.exists():data=target.read_bytes()
        else:
            req=urllib.request.Request(row['source_url'],headers={'User-Agent':'SSI-reproducibility-release/1.0'})
            with urllib.request.urlopen(req,timeout=120) as response:data=response.read()
        if hashlib.sha256(data).hexdigest()!=row['source_sha256']:
            raise SystemExit('Source snapshot changed: '+row['filename']+'. Retain the manuscript snapshot rather than silently replacing it.')
        if not target.exists():target.write_bytes(data)
        print('Verified '+row['filename'])
if __name__=='__main__':main()
