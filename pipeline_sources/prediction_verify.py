from pathlib import Path
import json
import numpy as np
import pandas as pd
OUT=Path('__LEGACY_ROOT__/work/ssi_new_prediction')
ROOT=OUT.parents[1]
panel=pd.read_csv(ROOT/'outputs/SSI_Publication_Project/reproducibility/annual_panel.csv.gz')
panel=panel[panel.panel=='Modern_SSI'].copy();panel['age']=panel['Age group'];panel['unit']=panel.site+'|'+panel.age+'|'+panel.procedure
lookup={(r.unit,int(r.year)):r for r in panel.itertuples()}
cohort=pd.read_csv(OUT/'lagged_prediction_cohort.csv.gz')
held=pd.read_csv(OUT/'heldout_predictions.csv')
checks=[]
assert not cohort.duplicated(['unit','year']).any()
assert not held.duplicated(['unit','year']).any()
checks.append('Unique unit-year rows in lagged cohort and heldout predictions.')
for r in cohort.itertuples():
 target=lookup[(r.unit,r.year)];prior=lookup[(r.unit,r.year-1)]
 assert target.n==r.n and target.y==r.y and np.isclose(target.e,r.e)
 assert prior.n==r.n_lag1 and prior.y==r.y_lag1 and np.isclose(prior.e,r.e_lag1)
 older=[lookup[(r.unit,j)] for j in range(r.year-3,r.year) if (r.unit,j) in lookup]
 assert sum(o.n for o in older)==r.history_n
 assert sum(o.y for o in older)==r.history_y
 assert np.isclose(sum(o.e for o in older),r.history_e)
 assert r.history_years==len(older)
 assert r.outcome==int(target.y>target.e)
 assert np.isclose(r.log_volume,np.log1p(prior.n))
 assert np.isclose(r.log_expected_rate,np.log((prior.e+.5)/(prior.n+1)))
 assert np.isclose(r.log_prior_sir,np.log((prior.y+.5)/(prior.e+.5)))
 assert np.isclose(r.log_history_sir,np.log((sum(o.y for o in older)+.5)/(sum(o.e for o in older)+.5)))
checks.append('All source target, prior and history fields independently reconstructed. Only t-3 to t-1 source predictors.')
ca=cohort[cohort.State=='California'];assert ca[ca['set']=='Training'].year.between(2017,2022).all();assert ca[ca['set']=='Test'].year.between(2023,2025).all()
ore=held[held.State=='Oregon'];assert (ore.year==2017).all();assert set(ore.site).isdisjoint(set(ca.site))
checks.append('Chronological California development/test split and separate Oregon hospital identities verified.')
cf=pd.read_csv(OUT/'model_coefficients.csv').set_index('term').estimate
scales=pd.read_csv(OUT/'training_feature_scaling.csv').set_index('feature')
lp=np.full(len(held),cf['(Intercept)'])
for term,val in cf.items():
 if term=='(Intercept)':continue
 if term.startswith('procedure'):lp+=(held.procedure==term[len('procedure'):]).to_numpy()*val
 elif term.startswith('age'):lp+=(held.age==term[len('age'):]).to_numpy()*val
 elif term.endswith('_z'):
  feat=term[:-2];lp+=((held[feat]-scales.loc[feat,'center'])/scales.loc[feat,'scale']).to_numpy()*val
 else:raise AssertionError(term)
p=1/(1+np.exp(-lp));max_prediction_error=float(np.max(np.abs(p-held.combined)))
assert max_prediction_error<5.1e-12
checks.append('Frozen R model probabilities independently reconstructed from coefficient table and feature scaling.')
metrics=pd.read_csv(OUT/'heldout_performance.csv')
curves=pd.read_csv(OUT/'ROC_PR_curve_coordinates.csv.gz')
auc_diffs=[]
for r in metrics.itertuples():
 if not np.isfinite(r.AUC):continue
 g=held[held['set']==r.dataset]
 if r.group in ['Adult','Pediatric']:g=g[g.age==r.group]
 elif r.group.startswith('Target year '):g=g[g.year==int(r.group.split()[-1])]
 elif r.group!='All ages and procedures':g=g[g.procedure==r.group]
 y=g.outcome.to_numpy();s=g[r.method].to_numpy();n1=y.sum();n0=len(y)-n1
 rank_auc=(pd.Series(s).rank(method='average').to_numpy()[y==1].sum()-n1*(n1+1)/2)/(n1*n0)
 cc=curves[(curves.dataset==r.dataset)&(curves.group==r.group)&(curves.method==r.method)]
 trap_auc=np.trapezoid(cc.TPR.to_numpy(),cc.FPR.to_numpy())
 auc_diffs.extend([abs(rank_auc-r.AUC),abs(trap_auc-r.AUC)])
 assert abs(rank_auc-r.AUC)<1e-12 and abs(trap_auc-r.AUC)<1e-12
 grouped=pd.DataFrame({'s':s,'y':y}).groupby('s',sort=True).agg(n=('y','size'),pos=('y','sum')).sort_index(ascending=False)
 cp=grouped.pos.cumsum();nn=grouped.n.cumsum()
 ap=((grouped.pos/n1)*(cp/nn)).sum()
 assert abs(ap-r.AP)<1e-12
checks.append('Every estimable pooled, subgroup and procedure AUC checked by independent rank formula and trapezoidal ROC integration. AP checked by grouped threshold formula.')
review=pd.read_csv(OUT/'review_capacity_results.csv')
assert ((review.alert_capture>=0)&(review.alert_capture<=1)).all()
assert ((review.precision>=0)&(review.precision<=1)).all()
assert np.allclose(review.alerts_selected_equivalent/review.total_alerts,review.alert_capture)
assert np.allclose(review.alerts_selected_equivalent/review.reports_reviewed_equivalent,review.precision)
checks.append('Review-capacity counts, capture and precision reconcile, with fractional boundary tie allocation.')
cal=pd.read_csv(OUT/'calibration_deciles.csv')
assert ((cal.observed_lower>=0)&(cal.observed_upper<=1)).all()
for (ds,gname),g in cal.groupby(['dataset','group']):
 m=metrics[(metrics.dataset==ds)&(metrics.group==gname)&(metrics.method=='combined')].iloc[0]
 assert g.reports.sum()==m.reports and g.alerts.sum()==m.alerts
checks.append('Calibration bins reconcile to evaluation report/alert totals and confidence bounds lie within 0 to 1.')
prohibited=set('\u2010\u2011\u2012\u2013\u2014\u2015\u2212\ufe58\ufe63\uff0d')
files=[]
for path in OUT.glob('*'):
 if path.suffix in ['.py','.R','.json','.txt','.csv','.log']:
  txt=path.read_text();bad=set(txt)&prohibited;assert not bad,(path,bad);files.append(path.name)
checks.append('All generated plain text, code and CSV files audited for prohibited dash/minus characters.')
audit={'status':'PASS','checks':checks,'heldout_probability_max_error':max_prediction_error,'AUC_max_error':max(auc_diffs),'plain_text_files_audited':files,'source_reconstructed_report_pairs':len(cohort),'heldout_rows':len(held),'California_test_rows':int((held['set']=='Test').sum()),'Oregon_rows':int((held['set']=='Oregon external').sum())}
(OUT/'independent_verification.json').write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps(audit,indent=2))
