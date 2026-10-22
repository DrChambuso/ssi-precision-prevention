from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
ROOT=Path('__LEGACY_ROOT__')
OUT=ROOT/'work/ssi_new_prediction'
PANEL=ROOT/'outputs/SSI_Publication_Project/reproducibility/annual_panel.csv.gz'
a=pd.read_csv(PANEL)
a=a[(a.panel=='Modern_SSI') & a['Age group'].isin(['Adult','Pediatric']) & a.State.isin(['California','Oregon'])].copy()
a=a[np.isfinite(a[['n','y','e']]).all(axis=1)&(a.n>0)&(a.y>=0)&(a.e>=0)].copy()
a['age']=a['Age group']
a['unit']=a.site+'|'+a.age+'|'+a.procedure
a=a.sort_values(['unit','year']).reset_index(drop=True)
assert not a.duplicated(['unit','year']).any()
pairs=a.copy()
for lag in (1,2,3):
    past=a[['unit','year','n','y','e']].copy()
    past.year+=lag
    past=past.rename(columns={c:f'{c}_lag{lag}' for c in ['n','y','e']})
    pairs=pairs.merge(past,on=['unit','year'],how='left',validate='one_to_one')
pairs=pairs[pairs.n_lag1.notna()].copy()
for c in ['n','y','e']:
    pairs['history_'+c]=pairs[[f'{c}_lag{k}' for k in (1,2,3)]].sum(axis=1)
pairs['history_years']=pairs[[f'n_lag{k}' for k in (1,2,3)]].notna().sum(axis=1)
pairs['prior_volume']=pairs.n_lag1
pairs['prior_cases']=pairs.y_lag1
pairs['prior_sir']=(pairs.y_lag1+.5)/(pairs.e_lag1+.5)
pairs['history_sir']=(pairs.history_y+.5)/(pairs.history_e+.5)
pairs['log_volume']=np.log1p(pairs.n_lag1)
pairs['log_expected_rate']=np.log((pairs.e_lag1+.5)/(pairs.n_lag1+1))
pairs['log_prior_sir']=np.log(pairs.prior_sir)
pairs['log_history_sir']=np.log(pairs.history_sir)
pairs['outcome']=(pairs.y>pairs.e).astype(int)
pairs['set']=np.where(pairs.State=='Oregon','Oregon external',np.where(pairs.year<=2022,'Training','Test'))
features=['log_volume','log_expected_rate','log_prior_sir','log_history_sir']
assert np.isfinite(pairs[features].to_numpy()).all()
assert pairs.loc[pairs.State=='California','year'].min()==2017
assert pairs.loc[pairs.State=='California','year'].max()==2025
pairs.to_csv(OUT/'lagged_prediction_cohort.csv.gz',index=False)
audit={'source_panel_sha256':hashlib.sha256(PANEL.read_bytes()).hexdigest(),'source_rows_CA':int((a.State=='California').sum()),'source_operations_CA':int(a.loc[a.State=='California','n'].sum()),'source_SSI_CA':int(a.loc[a.State=='California','y'].sum()),'source_predicted_CA':float(a.loc[a.State=='California','e'].sum()),'source_sites_CA':int(a.loc[a.State=='California','site'].nunique()),'prediction_outcome':'Target annual report has reported SSI count greater than source predicted SSI count (O>E). This is an annual report alert, not infection onset.','training':'California target years 2017-2022, Adult and Pediatric.','test':'California target years 2023-2025, Adult and Pediatric.','external':'Oregon target year 2017 with Oregon 2016 features; no hospital identity join to California. Same baseline era and common procedure labels.','feature_history':'Available reports in t-3 to t-1. Requires immediate previous year t-1. Missing older years contribute no unobserved values; aggregate only available history.','zero_expected':'Retained when nonnegative and finite; alert defined by count comparison and model predictors use half-count smoothing.','unit_definition':'Canonical State|county|hospital name, age group and procedure. Consecutive annual reports paired within this identity.','feature_list':features,'rounding':'Predicted and comparator scores rounded to 12 significant digits for exact ties.'}
(OUT/'cohort_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
cols=['set','State','age','year']
pairs.groupby(cols).agg(reports=('outcome','size'),alerts=('outcome','sum'),operations=('n','sum'),SSIs=('y','sum'),sites=('site','nunique'),prior_zero_expected=('e_lag1',lambda x:sum(x==0)),target_zero_expected=('e',lambda x:sum(x==0))).reset_index().to_csv(OUT/'cohort_counts_by_year_age.csv',index=False)
print(pairs.groupby('set').agg(reports=('outcome','size'),alerts=('outcome','sum'),operations=('n','sum'),SSIs=('y','sum'),sites=('site','nunique'),prior_zero_expected=('e_lag1',lambda x:sum(x==0)),target_zero_expected=('e',lambda x:sum(x==0))).to_string())
