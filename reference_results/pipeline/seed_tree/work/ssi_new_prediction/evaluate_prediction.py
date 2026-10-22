from pathlib import Path
import json
import numpy as np
import pandas as pd
OUT=Path('__LEGACY_ROOT__/work/ssi_new_prediction')
d=pd.read_csv(OUT/'heldout_predictions.csv')
B=250
METHODS=['prior_volume','prior_cases','prior_sir','combined']
NAMES={'prior_volume':'Prior operation volume','prior_cases':'Prior SSI count','prior_sir':'Smoothed prior observed/predicted SSI ratio','combined':'Combined model'}
rng=np.random.default_rng(20261016)
class Curve:
 def __init__(self,y,score):
  self.order=np.argsort(-score,kind='stable'); self.y=np.asarray(y)[self.order];self.score=np.asarray(score)[self.order]
  self.ends=np.r_[np.flatnonzero(np.diff(self.score)!=0)+1,len(y)]
  self.starts=np.r_[0,self.ends[:-1]]
 def counts(self,w):
  ww=np.asarray(w)[self.order]
  return np.add.reduceat(ww*self.y,self.starts),np.add.reduceat(ww*(1-self.y),self.starts)
 def metrics(self,w,budgets=(.1,.2,.3)):
  yp,yn=self.counts(w);totp=yp.sum();totn=yn.sum();tot=totp+totn
  if not(totp>0 and totn>0):return dict(AUC=np.nan,AP=np.nan,prevalence=totp/tot if tot else np.nan,**{f'capture_{int(b*100)}':np.nan for b in budgets})
  cp=np.cumsum(yp);cn=np.cumsum(yn);allcum=cp+cn
  auc=np.sum(yp*(totn-cn+.5*yn))/(totp*totn)
  ap=np.sum(yp/totp*cp/np.maximum(allcum,1))
  result={'AUC':auc,'AP':ap,'prevalence':totp/tot}
  for b in budgets:
   capacity=b*tot;idx=np.searchsorted(allcum,capacity,side='left')
   prev_total=allcum[idx-1] if idx>0 else 0;prevp=cp[idx-1] if idx>0 else 0
   frac=(capacity-prev_total)/(yp[idx]+yn[idx])
   selected_alerts=prevp+frac*yp[idx]
   result[f'capture_{int(b*100)}']=selected_alerts/totp
   result[f'precision_{int(b*100)}']=selected_alerts/capacity
   result[f'selected_alerts_{int(b*100)}']=selected_alerts
  return result
 def coordinates(self):
  yp,yn=self.counts(np.ones(len(self.y)));cp=np.cumsum(yp);cn=np.cumsum(yn);total=cp+cn
  return pd.DataFrame({'threshold':np.r_[np.inf,self.score[self.starts]],'FPR':np.r_[0,cn/yn.sum()],'TPR':np.r_[0,cp/yp.sum()],'recall':np.r_[0,cp/yp.sum()],'precision':np.r_[1,cp/total]})
def ci(a):
 a=np.asarray(a);a=a[np.isfinite(a)]
 return list(np.quantile(a,[.025,.975])) if len(a) else [np.nan,np.nan]
def groups_for(g):
 yield 'All ages and procedures',g
 for age in ['Adult','Pediatric']:yield age,g[g.age==age]
 for yr in sorted(g.year.unique()):yield f'Target year {yr}',g[g.year==yr]
 for proc in sorted(g.procedure.unique()):yield proc,g[g.procedure==proc]
metricsrows=[];reviewrows=[];rocs=[];calrows=[];deltarows=[]
for dataset in ['Test','Oregon external']:
 base=d[d['set']==dataset].copy().reset_index(drop=True)
 for label,g in groups_for(base):
  g=g.reset_index(drop=True);y=g.outcome.to_numpy();ns=len(g);K=g.site.nunique();one=np.ones(ns)
  if y.min()==y.max():
   for method in METHODS:metricsrows.append({'dataset':dataset,'group':label,'method':method,'reports':ns,'alerts':int(y.sum()),'sites':K,'operations':int(g.n.sum()),'SSI_cases':int(g.y.sum()),'AUC':np.nan,'AUC_lower':np.nan,'AUC_upper':np.nan,'AP':np.nan,'bootstrap_repeats':0})
   continue
  curves={m:Curve(y,g[m].to_numpy()) for m in METHODS}
  vals={m:curves[m].metrics(one) for m in METHODS}
  sites,siteindex=np.unique(g.site.to_numpy(),return_inverse=True)
  # Sample whole hospitals with replacement. Paired method comparisons share draws.
  weights=np.zeros((B,K),dtype=np.int16)
  for b in range(B):weights[b]=np.bincount(rng.integers(0,K,K),minlength=K)
  isoverall=label in ['All ages and procedures','Adult','Pediatric'] or label.startswith('Target year')
  samples={m:[] for m in METHODS if isoverall or m=='combined'}
  for b in range(B):
   ww=weights[b,siteindex]
   for m in samples:samples[m].append(curves[m].metrics(ww))
  for m in METHODS:
   v=vals[m];ss=pd.DataFrame(samples[m]) if m in samples else None
   row={'dataset':dataset,'group':label,'method':m,'method_label':NAMES[m],'reports':ns,'alerts':int(y.sum()),'sites':K,'operations':int(g.n.sum()),'SSI_cases':int(g.y.sum()),'AUC':v['AUC'],'AP':v['AP'],'prevalence':y.mean(),'bootstrap_repeats':B if m in samples else 0}
   for metric in ['AUC','AP']:
    row[metric+'_lower'],row[metric+'_upper']=ci(ss[metric]) if ss is not None else [np.nan,np.nan]
   metricsrows.append(row)
   cc=curves[m].coordinates();cc.insert(0,'method',m);cc.insert(0,'group',label);cc.insert(0,'dataset',dataset);rocs.append(cc)
   if isoverall:
    for cap in (10,20,30):
     r={'dataset':dataset,'group':label,'method':m,'capacity_fraction':cap/100,'reports_reviewed_equivalent':ns*cap/100,'alerts_selected_equivalent':v[f'selected_alerts_{cap}'],'alert_capture':v[f'capture_{cap}'],'precision':v[f'precision_{cap}'],'lift_over_random':v[f'capture_{cap}']/(cap/100),'total_reports':ns,'total_alerts':int(y.sum())}
     r['capture_lower'],r['capture_upper']=ci(ss[f'capture_{cap}'])
     r['precision_lower'],r['precision_upper']=ci(ss[f'precision_{cap}'])
     reviewrows.append(r)
  if isoverall:
   cmb=pd.DataFrame(samples['combined'])
   for comparator in METHODS[:-1]:
    comp=pd.DataFrame(samples[comparator])
    for metric in ['AUC','AP','capture_10','capture_20','capture_30']:
     lo,hi=ci(cmb[metric]-comp[metric])
     deltarows.append({'dataset':dataset,'group':label,'comparator':comparator,'metric':metric,'difference_combined_minus_comparator':vals['combined'][metric]-vals[comparator][metric],'lower':lo,'upper':hi})
   # Fixed prediction deciles; cluster bootstrap only resamples sites.
   p=g.combined.to_numpy();cuts=np.unique(np.quantile(p,np.linspace(0,1,11)))
   bins=np.searchsorted(cuts[1:-1],p,side='right')
   for bn in sorted(np.unique(bins)):
    sel=bins==bn;ob=y[sel].mean();pred=p[sel].mean()
    obsdraw=[]
    for b in range(B):
     ww=weights[b,siteindex][sel]
     obsdraw.append(np.sum(ww*y[sel])/ww.sum() if ww.sum() else np.nan)
    lo,hi=ci(obsdraw)
    calrows.append({'dataset':dataset,'group':label,'bin':int(bn+1),'reports':int(sel.sum()),'alerts':int(y[sel].sum()),'mean_prediction':pred,'observed_alert_fraction':ob,'observed_lower':lo,'observed_upper':hi,'prediction_min':p[sel].min(),'prediction_max':p[sel].max()})
   # Overall probabilistic loss is meaningful only for combined model probabilities.
   brier=np.mean((p-y)**2);logloss=-np.mean(y*np.log(p)+(1-y)*np.log1p(-p))
   draws=[]
   for b in range(B):
    ww=weights[b,siteindex]
    draws.append({'Brier':np.average((p-y)**2,weights=ww),'log_loss':np.average(-y*np.log(p)-(1-y)*np.log1p(-p),weights=ww)})
   draws=pd.DataFrame(draws)
   for metric,point in [('Brier',brier),('log_loss',logloss)]:
    lo,hi=ci(draws[metric])
    deltarows.append({'dataset':dataset,'group':label,'comparator':'Probability loss of combined model','metric':metric,'difference_combined_minus_comparator':point,'lower':lo,'upper':hi})
pd.DataFrame(metricsrows).to_csv(OUT/'heldout_performance.csv',index=False)
pd.DataFrame(reviewrows).to_csv(OUT/'review_capacity_results.csv',index=False)
pd.concat(rocs,ignore_index=True).to_csv(OUT/'ROC_PR_curve_coordinates.csv.gz',index=False)
pd.DataFrame(calrows).to_csv(OUT/'calibration_deciles.csv',index=False)
pd.DataFrame(deltarows).to_csv(OUT/'paired_method_comparisons_and_losses.csv',index=False)
summary={'bootstrap_repeats':B,'bootstrap_unit':'Named site, with all age groups, procedures and years resampled together within each evaluated population.','CI':'Percentile 95% site-cluster bootstrap confidence interval.','review_budget_ties':'At each exact report review capacity, equal-score reports at the boundary contribute fractionally, giving expected alert capture under uniform random selection within that score tie. This avoids arbitrary sorting of tied comparator values.','AP':'Average precision, using distinct score thresholds and stepwise recall increments.','calibration':'Observed report-alert fraction by prediction decile, with site-cluster confidence intervals. Predictions remain frozen from training; no recalibration applied.','evaluation':'Repeated annual reports remain grouped within site for uncertainty. Counts of procedures/SSI events describe exposure, and are not independent prediction sample size.'}
(OUT/'evaluation_methods.json').write_text(json.dumps(summary,indent=2)+'\n')
print(pd.DataFrame(metricsrows).query("group == 'All ages and procedures'").to_string(index=False))
print(pd.DataFrame(reviewrows).query("group == 'All ages and procedures' and method == 'combined'").to_string(index=False))
