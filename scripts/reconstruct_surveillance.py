#!/usr/bin/env python3
"""Reaggregate supplied source rows; optionally verify every row against original CSVs."""
from pathlib import Path
import argparse,csv,hashlib,json,platform,re,time
import numpy as np
import pandas as pd

KEY=['hospital_procedure_age_id','reporting_year']
COUNTS=['operations','ssi_cases','predicted_ssi_cases']

def aggregate_rows(rows):
    if rows.duplicated(['source_file','source_row']).any():
        raise ValueError('Duplicate original source location')
    if rows.duplicated('source_record_id').any():
        raise ValueError('Duplicate source record ID')
    if rows[COUNTS].isna().any().any():
        raise ValueError('Missing count in eligible analysis source rows')
    if (rows.operations<=0).any() or (rows.ssi_cases<0).any() or (rows.ssi_cases>rows.operations).any() or (rows.predicted_ssi_cases<0).any():
        raise ValueError('Invalid eligible count')
    return rows.groupby(KEY,sort=True,dropna=False).agg(
        operations=('operations','sum'),ssi_cases=('ssi_cases','sum'),
        predicted_ssi_cases=('predicted_ssi_cases','sum'),source_rows_combined=('source_record_id','size')).reset_index()

def verify_raw(rows,source_dir,manifest):
    results=[]
    for r in manifest.to_dict('records'):
        p=source_dir/r['filename']; digest=hashlib.sha256(p.read_bytes()).hexdigest()
        if digest!=r['source_sha256']:raise ValueError('Raw source hash differs: '+r['filename'])
        with p.open(encoding=r['encoding'],newline='') as handle: original=list(csv.DictReader(handle))
        subset=rows[rows.source_file==r['filename']]
        def scalar(v):
            try:return float(str(v).replace(',',''))
            except (ValueError,TypeError):return float('nan')
        for q in subset.to_dict('records'):
            x=original[int(q['source_row'])-1]
            actual=[scalar(x.get('Procedure_Count',x.get('Procedures Performed'))),
                    scalar(x.get('Infections_Reported',x.get('Infection_Count',x.get('Observed Infections')))),
                    scalar(x.get('Infections_Predicted',x.get('Predicted_Infection_Count',x.get('Predicted Infections'))))]
            expected=[q[c] for c in COUNTS]
            if not np.allclose(actual,expected,rtol=0,atol=1e-12,equal_nan=True):
                raise ValueError(f"Raw count mismatch: {r['filename']} data row {q['source_row']}")
        results.append({'filename':r['filename'],'sha256':digest,'verified_rows':len(subset)})
    if sum(x['verified_rows'] for x in results)!=len(rows):raise ValueError('Raw verification incomplete')
    return results

def run(root,source_dir=None,output=None):
    start=time.perf_counter(); root=Path(root)
    master=pd.read_csv(root/'data/derived/SSI_annual_reports_2016_2025.csv.gz',low_memory=False)
    rows=pd.read_csv(root/'data/derived/California_source_rows.csv.gz',dtype={'source_record_id':str,'source_facility_id':str,'reporting_period':str},low_memory=False)
    rebuilt=aggregate_rows(rows)
    if master.duplicated(KEY).any():raise ValueError('Duplicate annual key')
    joined=master.merge(rebuilt,on=KEY,validate='one_to_one',suffixes=('_master','_rebuilt'))
    if len(joined)!=len(master) or len(rebuilt)!=len(master):raise ValueError('Annual population mismatch')
    checks={}
    for c in COUNTS+['source_rows_combined']:
        delta=np.abs(joined[c+'_master']-joined[c+'_rebuilt'])
        checks[c]={'pass':bool((delta<=1e-12).all()),'maximum_absolute_difference':float(delta.max())}
    # Calendar-year matching, including missing years, independently checks the archived lag columns.
    lag_names={1:'previous_year',2:'two_years_earlier',3:'three_years_earlier'}
    for lag,label in lag_names.items():
        past=master[KEY+COUNTS].copy();past.reporting_year+=lag
        v=master.merge(past,on=KEY,how='left',validate='one_to_one',suffixes=('','_check'))
        for c in COUNTS:
            name=label+'_'+c
            if name not in master:continue
            # Third lags were populated only for prediction-eligible records.
            mask=v.prediction_analysis_eligible.eq(1) if lag==3 else np.ones(len(v),dtype=bool)
            a=v.loc[mask,name].to_numpy(float);b=v.loc[mask,c+'_check'].to_numpy(float)
            checks[name]={'pass':bool(np.allclose(a,b,atol=1e-12,rtol=0,equal_nan=True))}
    checks['signal_rule']={'pass':bool(master.above_predicted_ssi_signal.eq(master.ssi_cases.gt(master.predicted_ssi_cases).astype(int)).all())}
    checks['zero_predicted_ratio_rule']={'pass':bool(master.observed_to_predicted_ssi_ratio.isna().equals(master.predicted_ssi_cases.eq(0)))}
    checks['eligible_values']={'pass':bool(((master.operations>0)&(master.ssi_cases>=0)&(master.ssi_cases<=master.operations)&(master.predicted_ssi_cases>=0)).all())}
    counts={'source_rows':len(rows),'annual_reports':len(master),'operations':int(master.operations.sum()),'ssis':int(master.ssi_cases.sum()),'hospitals':int(master.hospital_id.nunique()),'procedures':int(master.surgical_procedure.nunique()),'signals':int(master.above_predicted_ssi_signal.sum()),'two_half_year_annual_reports':int(master.source_rows_combined.eq(2).sum())}
    expected={'source_rows':78583,'annual_reports':72854,'operations':6737972,'ssis':37525,'hospitals':469,'procedures':28,'signals':12032,'two_half_year_annual_reports':5729}
    checks['population_totals']={'pass':counts==expected}
    manifest=pd.read_csv(root/'provenance/california_source_manifest.csv')
    rawcheck=verify_raw(rows,Path(source_dir),manifest) if source_dir else []
    issues=[k for k,v in checks.items() if not v['pass']]
    result={'passed':not issues,'counts':counts,'checks':checks,'issues':issues,'raw_source_files_verified_this_run':rawcheck,'raw_source_validation': 'all original counts and hashes verified' if source_dir else 'not requested; this run starts with supplied source-row extraction','seconds':time.perf_counter()-start,'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__}
    destination=Path(output) if output else root/'validation/surveillance_reconstruction.json'
    destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'passed':result['passed'],'counts':counts,'raw_files_verified':len(rawcheck),'seconds':result['seconds']},indent=2))
    if issues:raise SystemExit('Reconstruction failed: '+', '.join(issues))
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--source-dir',type=Path,help='Directory containing original source CSVs, optional for offline run')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args();run(args.root,args.source_dir,args.output)
