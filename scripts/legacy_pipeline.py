#!/usr/bin/env python3
"""Run archived study equations in an isolated, release-local workspace.

Seeded reference results permit isolated-stage testing. They are not evidence
that all seeded files were recomputed. The execution ledger records actual runs.
"""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'provenance/pipeline_manifest.json'
PLOT='outputs/SSI_Prevention_Intelligence/SSI_Inferential_Microbiology_Figures'
INTEGRATED='outputs/SSI_Prevention_Intelligence/SSI_Integrated_Publication_Revision'

def sha(data): return hashlib.sha256(data).hexdigest()
def manifest(): return json.loads(MANIFEST.read_text())
@contextmanager
def ledger_lock(workspace):
    # fcntl is available on the documented Linux/macOS targets.
    import fcntl
    with (workspace/'execution_ledger.lock').open('a') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX)
        try: yield
        finally: fcntl.flock(handle,fcntl.LOCK_UN)
def safe_workspace(value):
    p=Path(value).resolve()
    if not p.is_relative_to((ROOT/'results').resolve()):
        raise ValueError('Workspace must be inside the release results directory.')
    return p

def normalize_runtime(text, workspace, source_root):
    text=text.replace('__LEGACY_ROOT__',workspace.as_posix())
    text=text.replace('__SOURCE_ROOT__',source_root.as_posix())
    return text

def initialize(workspace, source_root):
    workspace.mkdir(parents=True,exist_ok=True)
    copied=0
    for row in manifest()['seeds']:
        source=ROOT/row['stored_path'];dest=workspace/row['workspace_path']
        if dest.exists(): continue
        data=source.read_bytes()
        if row['gzip_encoded_for_storage']: data=gzip.decompress(data)
        if sha(data)!=row['distributed_content_sha256']:
            raise ValueError('Seed checksum mismatch: '+row['stored_path'])
        if dest.suffix in ('.py','.R'):
            text=data.decode('utf-8')
            # This evaluator alias was historically imported by the diagnostics.
            data=normalize_runtime(text,workspace,source_root).encode('utf-8')
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);copied+=1
    for d in ('work/ssi_new_prediction','work/ssi_inferential_stats','work/ssi_inferential_microbiology',PLOT+'/individual_vector_pdfs',INTEGRATED+'/tables/microbiology','logs','runtime_sources'):
        (workspace/d).mkdir(parents=True,exist_ok=True)
    sync_plot_tables(workspace)
    return copied

def sync_plot_tables(workspace):
    """Expose generated numerical outputs at the legacy plotting read locations."""
    for src,dests in [
      ('work/ssi_new_prediction',[PLOT+'/reproducibility/prediction']),
      ('work/ssi_inferential_stats',[PLOT+'/tables/statistics']),
      ('work/ssi_inferential_microbiology',[PLOT+'/tables/microbiology',INTEGRATED+'/tables/microbiology'])]:
        source=workspace/src
        if not source.exists(): continue
        for rel in dests:
            dest=workspace/rel;dest.mkdir(parents=True,exist_ok=True)
            for p in source.iterdir():
                if p.is_file() and p.suffix in ('.csv','.gz','.json','.rds'):
                    shutil.copy2(p,dest/p.name)

def plan(ids,with_dependencies):
    stages={x['id']:x for x in manifest()['scripts']};selected=[]
    def visit(id):
        if id not in stages: raise ValueError('Unknown stage: '+id)
        if id in selected:return
        if with_dependencies:
            for dependency in stages[id]['dependencies']:visit(dependency)
        selected.append(id)
    for id in ids:visit(id)
    return [stages[id] for id in selected]

def run(stages,workspace,source_root):
    initialize(workspace,source_root)
    ledger_path=workspace/'execution_ledger.json'
    for row in stages:
        if row['external_source_required'] and not source_root.is_dir():
            raise FileNotFoundError('This stage requires --source-root containing the documented original NHSN source tree. Archived extracted tables are already available for microbiology_tables and microbiology_exact.')
        source=ROOT/row['path'];data=source.read_bytes()
        if sha(data)!=row['distributed_sha256']:raise ValueError('Source checksum mismatch: '+row['path'])
        text=normalize_runtime(data.decode('utf-8'),workspace,source_root)
        if '__LEGACY_ROOT__' in text or '__SOURCE_ROOT__' in text:raise ValueError('Unresolved path token')
        runtime=workspace/'runtime_sources'/source.name;runtime.write_text(text)
        if row['language']=='R':
            executable=os.environ.get('RSCRIPT','Rscript')
            if not shutil.which(executable):raise RuntimeError('Rscript is required; see environment instructions.')
        else:executable=sys.executable
        log=workspace/'logs'/(row['id']+'.log')
        started=time.time()
        print('Running '+row['id']+'; log '+str(log.relative_to(ROOT)),flush=True)
        with log.open('w') as stream:
            proc=subprocess.run([executable,str(runtime)],cwd=workspace,stdout=stream,stderr=subprocess.STDOUT,env=os.environ.copy())
        entry={'stage':row['id'],'source_sha256':row['distributed_sha256'],'runtime_source_sha256':sha(runtime.read_bytes()),'exit_code':proc.returncode,'elapsed_seconds':round(time.time()-started,3),'log':str(log.relative_to(ROOT)),'status':'completed' if proc.returncode==0 else 'failed','reference_seeded':True,'interpretation':'This entry confirms this script execution only;seeded outputs of other stages were not recomputed.'}
        with ledger_lock(workspace):
            ledger=json.loads(ledger_path.read_text()) if ledger_path.exists() else []
            ledger.append(entry);ledger_path.write_text(json.dumps(ledger,indent=2)+'\n')
        if proc.returncode:
            print(log.read_text()[-10000:]);raise RuntimeError('Stage failed: '+row['id'])
        if row['id'] in ('case_bootstrap','survival_absolute'):
            name='future_SSI_case_capture_comparisons.csv' if row['id']=='case_bootstrap' else 'five_year_signal_probability_differences.csv'
            shutil.copy2(workspace/PLOT/'tables/statistics'/name,workspace/'work/ssi_inferential_stats'/name)
        sync_plot_tables(workspace)
        print('Completed '+row['id']+' in '+str(entry['elapsed_seconds'])+' seconds',flush=True)

def compare(workspace,relative,atol):
    import numpy as np
    import pandas as pd
    row=next((s for s in manifest()['seeds'] if s['workspace_path']==relative),None)
    if row is None:raise ValueError('No archived reference for '+relative)
    import io
    raw=(ROOT/row['stored_path']).read_bytes()
    if row['gzip_encoded_for_storage']:raw=gzip.decompress(raw)
    ref=pd.read_csv(io.BytesIO(raw));actual=pd.read_csv(workspace/relative)
    if ref.shape!=actual.shape or list(ref.columns)!=list(actual.columns):raise AssertionError('Table shape/columns differ')
    max_error=0.0;numeric=0
    for c in ref:
        if pd.api.types.is_numeric_dtype(ref[c]) and pd.api.types.is_numeric_dtype(actual[c]):
            a=ref[c].to_numpy(float);b=actual[c].to_numpy(float)
            if not np.array_equal(np.isnan(a),np.isnan(b)):raise AssertionError('Missingness differs: '+c)
            if not np.allclose(a,b,atol=atol,rtol=atol,equal_nan=True):raise AssertionError('Numeric values differ: '+c)
            finite=np.isfinite(a)&np.isfinite(b)
            if finite.any():max_error=max(max_error,float(np.max(np.abs(a[finite]-b[finite]))))
            numeric+=1
        elif ref[c].fillna('').astype(str).tolist()!=actual[c].fillna('').astype(str).tolist():raise AssertionError('Text/order differs: '+c)
    result={'table':relative,'rows':len(ref),'numeric_columns':numeric,'maximum_absolute_difference':max_error,'absolute_and_relative_tolerance':atol,'status':'passed'}
    dest=workspace/'comparisons';dest.mkdir(exist_ok=True)
    (dest/(Path(relative).stem+'.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['list','initialize','run','compare'])
    parser.add_argument('--stage',action='append',default=[])
    parser.add_argument('--with-dependencies',action='store_true')
    parser.add_argument('--workspace',default=str(ROOT/'results/legacy_workspace'))
    parser.add_argument('--source-root',default=str(ROOT/'data/raw/source_archive'))
    parser.add_argument('--table')
    parser.add_argument('--atol',type=float,default=1e-7)
    args=parser.parse_args();workspace=safe_workspace(args.workspace);source_root=Path(args.source_root).resolve()
    if args.command=='list':
        for s in manifest()['scripts']:print(s['id']+' ['+s['language']+'] '+s['description'])
    elif args.command=='initialize':print('Initialized '+str(initialize(workspace,source_root))+' selected aggregate input/reference files.')
    elif args.command=='run':
        if not args.stage:parser.error('At least one --stage is required.')
        run(plan(args.stage,args.with_dependencies),workspace,source_root)
    else:
        if not args.table:parser.error('--table is required for compare.')
        compare(workspace,args.table,args.atol)
if __name__=='__main__':main()
