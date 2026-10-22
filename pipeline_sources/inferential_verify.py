from pathlib import Path
from itertools import combinations
import json, math
import numpy as np
import pandas as pd

OUT=Path('__LEGACY_ROOT__/work/ssi_inferential_stats')
audit={}

# Independent implementation of the hospital-robust covariance for the pooled memory GLM.
d=pd.read_csv(OUT/'memory_GLM_score_verification_design.csv')
cols=list(d.columns[4:]);X=d[cols].to_numpy();y=d.alert.to_numpy();mu=d.fitted_value.to_numpy()
bread=np.linalg.inv(X.T@(X*mu[:,None]))
score=X*(y-mu)[:,None]
site,si=np.unique(d.site,return_inverse=True)
U=np.zeros((len(site),X.shape[1]));np.add.at(U,si,score)
N,P=X.shape;K=len(site)
V=bread@(U.T@U)@bread*(K/(K-1))*((N-1)/(N-P))
coef=pd.read_csv(OUT/'all_site_robust_GLM_coefficients.csv')
coef=coef[coef.model=='Next_report_alert_two_year_memory_adjusted'].set_index('term')
errors=[]
for j,c in enumerate(cols):
    errors.append(abs(np.sqrt(V[j,j])-coef.loc[c,'robust_SE']))
audit['independent_memory_GLM_robust_SE_max_error']=max(errors)
assert max(errors)<1e-8
audit['memory_score_stationarity_max_abs']=float(np.abs(score.sum(axis=0)).max())

# Recompute covariance independently for the nonoverlapping earlier-context sensitivity as well.
d=pd.read_csv(OUT/'earlier_service_context_Poisson_verification_design.csv')
cols=list(d.columns[4:]);X=d[cols].to_numpy();y=d.alert.to_numpy();mu=d.fitted_value.to_numpy()
bread=np.linalg.inv(X.T@(X*mu[:,None]));score=X*(y-mu)[:,None]
site,si=np.unique(d.site,return_inverse=True);U=np.zeros((len(site),X.shape[1]));np.add.at(U,si,score)
N,P=X.shape;K=len(site);V=bread@(U.T@U)@bread*K/(K-1)*(N-1)/(N-P)
coef=pd.read_csv(OUT/'earlier_service_context_all_coefficients.csv')
coef=coef[coef.model=='Poisson'].set_index('term')
errors=[abs(np.sqrt(V[j,j])-coef.loc[c,'robust_SE']) for j,c in enumerate(cols)]
audit['independent_earlier_context_GLM_robust_SE_max_error']=max(errors)
assert max(errors)<1e-8
audit['earlier_context_score_stationarity_max_abs']=float(np.abs(score.sum(axis=0)).max())

src=OUT.parents[1]/'outputs/SSI_Prevention_Intelligence/SSI_Signal_Memory_Vector_Atlas/reproducibility/annual_reports.csv.gz'
annual=pd.read_csv(src)
forward=pd.read_csv(OUT/'earlier_service_context_analysis_cohort.csv',dtype={'history':str})
assert not forward.duplicated(['unit','year']).any()
assert forward.year.between(2022,2025).all()
baseline=annual[annual.year.between(2016,2019)].groupby('unit')[['n','y','e']].sum()
for c in ['n','y','e']:
    assert np.allclose(forward['baseline_'+c],baseline[c].reindex(forward.unit).to_numpy(),rtol=0,atol=1e-8)
lookup=annual.set_index(['unit','year']).alert.to_dict()
for row in forward.itertuples():
    expected=str(lookup[(row.unit,row.year-2)])+str(lookup[(row.unit,row.year-1)])
    assert row.history.zfill(2)==expected
audit['earlier_context_population_and_nonoverlapping_history_independently_verified']=True

# Exact conditional logistic likelihood check and hospital-level sandwich score calculation.
d=pd.read_csv(OUT/'within_unit_exact_design.csv')
coef=pd.read_csv(OUT/'within_unit_exact_coefficients.csv')
cols=coef.term.tolist();b=coef.coefficient.to_numpy();X=d[cols].to_numpy();y=d.alert.to_numpy()
site,si=np.unique(d.site,return_inverse=True);U=np.zeros((len(site),len(b)));H=np.zeros((len(b),len(b)))
ll=0;combo_count=0
for unit,idx in d.groupby('unit',sort=False).indices.items():
    xx=X[idx];yy=y[idx];m=int(yy.sum());n=len(idx)
    assert 0<m<n
    assignments=np.asarray(list(combinations(range(n),m)),dtype=int)
    sums=xx[assignments].sum(axis=1)
    eta=sums@b;shift=eta.max();w=np.exp(eta-shift);w/=w.sum()
    expected=w@sums
    observed=yy@xx
    unit_score=observed-expected
    centered=sums-expected
    H+=centered.T@(centered*w[:,None])
    U[si[idx[0]]]+=unit_score
    ll+=float(observed@b-(shift+np.log(np.exp(eta-shift).sum())))
    combo_count+=len(assignments)
M=d.unit.nunique();K=len(site);P=len(b);Hinv=np.linalg.inv(H)
V=Hinv@(U.T@U)@Hinv*K/(K-1)*(M-1)/(M-P)
rows=[]
for j,c in enumerate(cols):
    se=np.sqrt(V[j,j]);z=b[j]/se
    rows.append({'term':c,'conditional_OR':np.exp(b[j]),'lower':np.exp(b[j]-1.96*se),'upper':np.exp(b[j]+1.96*se),
                 'robust_SE':se,'p':math.erfc(abs(z)/math.sqrt(2)),'reports':len(d),'units':M,'sites':K,'alerts':int(y.sum())})
pd.DataFrame(rows).to_csv(OUT/'within_unit_memory_exact_conditional_site_robust_OR.csv',index=False)
audit['exact_conditional_units']=M
audit['exact_conditional_reports']=len(d)
audit['exact_conditional_sites']=K
audit['exact_conditional_assignment_count']=combo_count
audit['exact_conditional_log_likelihood']=ll
audit['exact_conditional_score_stationarity_max_abs']=float(np.abs(U.sum(axis=0)).max())
audit['exact_conditional_information_SE_max_error']=float(np.max(np.abs(np.sqrt(Hinv.diagonal())-coef.model_SE.to_numpy())))
assert audit['exact_conditional_information_SE_max_error']<1e-7
assert audit['exact_conditional_score_stationarity_max_abs']<1e-3

# Numerical bounds and interval coherence across the delivered primary tables.
for file in ['procedure_prior_alert_adjusted_RR.csv','procedure_early_late_adjusted_IRR.csv','procedure_pediatric_adult_adjusted_IRR.csv','procedure_annual_trend_adjusted_IRR.csv','family_prior_signal_associations.csv']:
    q=pd.read_csv(OUT/file)
    assert np.isfinite(q[['effect','lower','upper','p']]).all().all()
    assert ((q.lower<=q.effect)&(q.effect<=q.upper)&(q.lower>0)&q.p.between(0,1)).all()
    assert (q.sites>=30).all()
audit['primary_effect_tables_finite_and_interval_ordered']=True
for file in ['time_to_alert_cluster_adjusted_HR.csv','time_varying_high_baseline_HR.csv','four_baseline_states_adjusted_Cox_HR.csv','four_baseline_states_time_varying_Cox_HR.csv']:
    q=pd.read_csv(OUT/file)
    assert np.isfinite(q[['HR','lower','upper','p']]).all().all()
    assert ((q.lower<=q.HR)&(q.HR<=q.upper)&(q.lower>0)&q.p.between(0,1)).all()
audit['survival_estimates_finite_and_interval_ordered']=True
q=pd.read_csv(OUT/'prediction_paired_comparisons_1999_cluster_bootstrap.csv')
assert q.p_centered_bootstrap.between(.0005,1).all()
assert (q.valid_draws>=.9*1999).all()
audit['paired_bootstrap_P_valid_and_at_least_90_percent_valid_draws']=True
prohibited=[chr(c) for c in [0x2010,0x2011,0x2012,0x2013,0x2014,0x2015,0x2212]]
bad=[]
for p in OUT.iterdir():
    if p.suffix in ['.csv','.txt','.json','.py','.R','.log']:
        txt=p.read_text(errors='replace')
        if any(c in txt for c in prohibited):bad.append(p.name)
audit['prohibited_dash_files']=bad
assert not bad,bad
(OUT/'independent_inferential_verification.json').write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps(audit,indent=2))
