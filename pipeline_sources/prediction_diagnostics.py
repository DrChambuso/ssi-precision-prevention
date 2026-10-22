from pathlib import Path
import numpy as np
import pandas as pd
OUT=Path('__LEGACY_ROOT__/work/ssi_new_prediction')
d=pd.read_csv(OUT/'heldout_predictions.csv')
# Load existing evaluator definitions without re-running cohort evaluations.
ns={};txt=(OUT/'evaluate_prediction.py').read_text();exec(txt[:txt.index('metricsrows=[]')],ns)
Curve=ns['Curve'];groups_for=ns['groups_for']
rows=[];diag=[]
def solve(x,y,offset=None):
 beta=np.zeros(x.shape[1]);offset=np.zeros(len(y)) if offset is None else offset
 for _ in range(100):
  eta=x@beta+offset;p=1/(1+np.exp(-eta));w=np.maximum(p*(1-p),1e-9)
  grad=x.T@(y-p);hess=(x.T*w)@x
  step=np.linalg.solve(hess,grad);beta+=step
  if np.max(np.abs(step))<1e-10:return beta
 raise RuntimeError('Calibration diagnostic did not converge')
for dataset in ['Test','Oregon external']:
 base=d[d['set']==dataset]
 for label,g in groups_for(base):
  if label not in ['All ages and procedures','Adult','Pediatric'] and not label.startswith('Target year'):continue
  y=g.outcome.to_numpy();one=np.ones(len(g));p=g.combined.to_numpy();lp=np.log(p/(1-p))
  if y.min()==y.max():continue
  for method in ns['METHODS']:
   c=Curve(y,g[method].to_numpy())
   for cap in np.linspace(.01,1,100):
    yy,nn=c.counts(one);cp=yy.cumsum();total=(yy+nn).cumsum();idx=min(np.searchsorted(total,cap*len(g)),len(total)-1)
    prev=total[idx-1] if idx else 0;pr=cp[idx-1] if idx else 0
    found=pr+(cap*len(g)-prev)/(yy[idx]+nn[idx])*yy[idx]
    rows.append({'dataset':dataset,'group':label,'method':method,'review_fraction':cap,'alert_capture':found/y.sum(),'precision':found/(cap*len(g)),'alerts_selected_equivalent':found})
  intercept=solve(one[:,None],y,lp)[0]
  joint=solve(np.column_stack([one,lp]),y)
  diag.append({'dataset':dataset,'group':label,'reports':len(y),'alerts':int(y.sum()),'mean_prediction':p.mean(),'observed_fraction':y.mean(),'Brier':np.mean((p-y)**2),'log_loss':np.mean(-y*np.log(p)-(1-y)*np.log1p(-p)),'calibration_intercept_slope_fixed_1':intercept,'calibration_intercept_slope_free':joint[0],'calibration_slope':joint[1],'recalibration_applied':False})
pd.DataFrame(rows).to_csv(OUT/'review_capacity_curve.csv',index=False)
pd.DataFrame(diag).to_csv(OUT/'calibration_global_diagnostics.csv',index=False)
print(pd.DataFrame(diag).to_string(index=False))
