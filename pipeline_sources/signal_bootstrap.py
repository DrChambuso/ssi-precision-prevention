from pathlib import Path
import json, math
import numpy as np
import pandas as pd

ROOT=Path('__LEGACY_ROOT__')
OUT=ROOT/'work/ssi_inferential_stats'
PRED=ROOT/'work/ssi_new_prediction/heldout_predictions.csv'
d=pd.read_csv(PRED)
B=1999
SEED=20261016
METHODS=['prior_volume','prior_cases','prior_sir','combined']
METRICS=['AUC','AP','capture_10','capture_20','capture_30']
rng=np.random.default_rng(SEED)

class Curve:
    def __init__(self,y,score):
        order=np.argsort(-np.asarray(score),kind='stable')
        self.order=order;self.y=np.asarray(y)[order];self.score=np.asarray(score)[order]
        self.ends=np.r_[np.flatnonzero(np.diff(self.score)!=0)+1,len(y)]
        self.starts=np.r_[0,self.ends[:-1]]
    def metrics(self,w):
        ww=np.asarray(w)[self.order]
        yp=np.add.reduceat(ww*self.y,self.starts)
        yn=np.add.reduceat(ww*(1-self.y),self.starts)
        tp=yp.sum();tn=yn.sum();tot=tp+tn
        if tp<=0 or tn<=0:
            return np.full(5,np.nan)
        cp=np.cumsum(yp);cn=np.cumsum(yn);ct=cp+cn
        auc=np.sum(yp*(tn-cn+.5*yn))/(tp*tn)
        ap=np.sum(yp/tp*cp/np.maximum(ct,1))
        vals=[auc,ap]
        for budget in (.1,.2,.3):
            capacity=budget*tot
            idx=min(np.searchsorted(ct,capacity,side='left'),len(ct)-1)
            prev=ct[idx-1] if idx else 0
            prevp=cp[idx-1] if idx else 0
            captured=prevp+(capacity-prev)/(yp[idx]+yn[idx])*yp[idx]
            vals.append(captured/tp)
        return np.asarray(vals)

def infer(samples,estimate,null=0):
    a=np.asarray(samples);a=a[np.isfinite(a)]
    if len(a)<.9*B:
        return dict(lower=np.nan,upper=np.nan,bootstrap_SE=np.nan,p_centered_bootstrap=np.nan,p_normal_bootstrap_SE=np.nan,valid_draws=len(a))
    se=np.std(a,ddof=1)
    # Shift the paired bootstrap distribution to the null. This is not a tail fraction of uncentered effects.
    p=(1+np.sum(np.abs(a-estimate)>=abs(estimate-null)))/(len(a)+1)
    pnorm=math.erfc(abs((estimate-null)/se)/math.sqrt(2)) if se>0 else float(estimate==null)
    low,high=np.quantile(a,[.025,.975])
    return dict(lower=low,upper=high,bootstrap_SE=se,p_centered_bootstrap=p,p_normal_bootstrap_SE=pnorm,valid_draws=len(a))

def bh(p,n=28):
    a=np.asarray(p,dtype=float);out=np.full(len(a),np.nan);ix=np.flatnonzero(np.isfinite(a));o=ix[np.argsort(a[ix])]
    if len(o):out[o]=np.minimum(1,np.minimum.accumulate((a[o]*n/np.arange(1,len(o)+1))[::-1])[::-1])
    return out

comparisons=[];singles=[];loss_rows=[];warnings=[]
for dataset in ['Test','Oregon external']:
    base=d[d['set']==dataset].copy()
    groups=[('All ages and procedures',base),('Adult',base[base.age=='Adult']),('Pediatric',base[base.age=='Pediatric'])]
    groups.extend((f'Target year {year}',g) for year,g in base.groupby('year'))
    if dataset=='Test':groups.extend((proc,g) for proc,g in base.groupby('procedure'))
    for group,g in groups:
        g=g.reset_index(drop=True)
        if len(g)<30 or g.outcome.nunique()!=2 or g.site.nunique()<10 or min(g.outcome.sum(),len(g)-g.outcome.sum())<5:
            warnings.append({'dataset':dataset,'group':group,'issue':'At least 30 reports, 10 sites, and 5 reports with each outcome required for bootstrap inference. Descriptive estimates remain available in the original prediction tables.'});continue
        y=g.outcome.to_numpy(dtype=float);one=np.ones(len(g));sites,si=np.unique(g.site,return_inverse=True);K=len(sites)
        curves={method:Curve(y,g[method].to_numpy()) for method in METHODS}
        point={method:curves[method].metrics(one) for method in METHODS}
        boot={method:np.full((B,len(METRICS)),np.nan) for method in METHODS}
        boot_prevalence=np.full(B,np.nan)
        # Draw each named hospital once with all its report rows across years, age groups, and procedures.
        for b in range(B):
            siteweights=np.bincount(rng.integers(0,K,K),minlength=K)
            rowweights=siteweights[si]
            boot_prevalence[b]=np.average(y,weights=rowweights)
            for method in METHODS:boot[method][b]=curves[method].metrics(rowweights)
        meta={'dataset':dataset,'group':group,'reports':len(g),'sites':K,'alerts':int(y.sum()),'operations':int(g.n.sum()),'SSI_cases':int(g.y.sum()),'bootstrap_repeats':B}
        for method in METHODS:
            for j,metric in enumerate(METRICS):
                null=.5 if metric=='AUC' else y.mean() if metric=='AP' else int(metric.split('_')[-1])/100
                inference=infer(boot[method][:,j],point[method][j],null)
                if metric=='AP':
                    adjusted=infer(boot[method][:,j]-boot_prevalence,point[method][j]-y.mean(),0)
                    for key in ['p_centered_bootstrap','p_normal_bootstrap_SE']:
                        inference[key]=adjusted[key]
                singles.append({**meta,'method':method,'metric':metric,'estimate':point[method][j],'null':null,**inference})
        for comparator in METHODS[:-1]:
            for j,metric in enumerate(METRICS):
                delta=point['combined'][j]-point[comparator][j]
                comparisons.append({**meta,'comparator':comparator,'metric':metric,'combined':point['combined'][j],
                    'comparator_estimate':point[comparator][j],'difference':delta,**infer(boot['combined'][:,j]-boot[comparator][:,j],delta)})
        print(dataset,group,len(g),K,'done',flush=True)

cmp=pd.DataFrame(comparisons);single=pd.DataFrame(singles)
cmp['q_BH']=np.nan;single['q_BH']=np.nan
# Procedure subgroup families: 28 procedures for each comparator and each metric, separate from pooled primary tests.
for metric in METRICS:
    for comparator in METHODS[:-1]:
        ix=(cmp.dataset=='Test')&cmp.group.isin(d.procedure.unique())&(cmp.metric==metric)&(cmp.comparator==comparator)
        cmp.loc[ix,'q_BH']=bh(cmp.loc[ix,'p_centered_bootstrap'])
    for method in METHODS:
        ix=(single.dataset=='Test')&single.group.isin(d.procedure.unique())&(single.metric==metric)&(single.method==method)
        single.loc[ix,'q_BH']=bh(single.loc[ix,'p_centered_bootstrap'])
cmp.to_csv(OUT/'prediction_paired_comparisons_1999_cluster_bootstrap.csv',index=False)
single.to_csv(OUT/'prediction_metrics_1999_cluster_bootstrap.csv',index=False)
pd.DataFrame(warnings,columns=['dataset','group','issue']).to_csv(OUT/'prediction_unavailable_groups.csv',index=False)
methods={'bootstrap_repeats':B,'random_seed':SEED,'resampling_unit':'Canonical named hospital site; all reports for each sampled site retained together. Identical hospital draws for paired prediction methods.',
         'confidence_intervals':'Percentile 95% confidence intervals from paired whole-site bootstrap.',
         'p_value':'Two-sided centered bootstrap: (1 + number of valid draws with abs(delta_star - observed_delta) >= abs(observed_delta - null))/(1 + number of valid draws). Null is zero for paired differences. This is not the fraction of uncentered bootstrap differences below zero.',
         'p_resolution':1/(B+1),'normal_bootstrap_SE_p':'Also supplied as a sensitivity calculation using the bootstrap standard error and standard normal approximation.',
         'single_method_nulls':'AUC 0.5, AP alert prevalence (AP minus prevalence re-estimated together in every bootstrap draw), and alert capture under random review equal to review capacity. Primary inferential model comparison is paired difference, rather than superiority to random review.',
         'capacity_ties':'Fractional random selection within boundary score ties, preserving exact expected review capacity for weighted samples.',
         'BH_families':'Procedure-level tests adjusted across 28 planned procedure tests separately for each comparator and metric, including unavailable procedures conservatively in the family size. Pooled, age and year tests are not mixed into those families.',
         'scope':'Frozen predictions are evaluated; bootstrap uncertainty describes test-site sampling conditional on the trained model, not training estimation uncertainty.',
         'external':'Oregon external target-year 2017 reports are evaluated independently from California.'}
(OUT/'prediction_inference_methods.json').write_text(json.dumps(methods,indent=2)+'\n')
print(cmp.query("group=='All ages and procedures'").to_string(index=False))
