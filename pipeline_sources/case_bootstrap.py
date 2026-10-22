from pathlib import Path
import numpy as np
import pandas as pd
B=Path('__LEGACY_ROOT__')/'outputs/SSI_Prevention_Intelligence/SSI_Inferential_Microbiology_Figures'
# A second operational endpoint: future SSI case capture rather than binary report alerts.
d=pd.read_csv(B/'reproducibility/prediction/heldout_predictions.csv')
d=d[d['set']=='Test'].copy();sites=sorted(d.site.unique());ix=pd.Categorical(d.site,categories=sites).codes
methods=['combined','prior_cases','prior_volume']
orders={m:np.unique(-d[m].to_numpy(),return_inverse=True)[1] for m in methods}
capacity=np.array([.1,.2,.3]);y=d.y.to_numpy(float)
def capture(m,w):
 inv=orders[m];nn=np.bincount(inv,weights=w);yy=np.bincount(inv,weights=w*y)
 cumulative_n=np.cumsum(nn);cumulative_y=np.cumsum(yy);out=[]
 for f in capacity:
  target=f*nn.sum();j=np.searchsorted(cumulative_n,target)
  before_n=cumulative_n[j-1] if j else 0;before_y=cumulative_y[j-1] if j else 0
  out.append((before_y+(target-before_n)/nn[j]*yy[j])/yy.sum())
 return np.array(out)
point={m:capture(m,np.ones(len(d))) for m in methods}
rng=np.random.default_rng(20261017);boots={m:[] for m in methods}
for i in range(1999):
 w=rng.multinomial(len(sites),np.repeat(1/len(sites),len(sites)))[ix]
 for m in methods:boots[m].append(capture(m,w))
boots={m:np.array(v) for m,v in boots.items()}
rows=[]
for m in methods[1:]:
 for j,f in enumerate(capacity):
  delta=point['combined'][j]-point[m][j];db=boots['combined'][:,j]-boots[m][:,j]
  p=(1+np.sum(np.abs(db-delta)>=abs(delta)))/2000
  lo,up=np.percentile(db,[2.5,97.5])
  rows.append(dict(comparator=m,capacity=f,combined_capture=point['combined'][j],comparator_capture=point[m][j],difference=delta,lower=lo,upper=up,p=p,reports=len(d),SSI_cases=int(d.y.sum()),sites=len(sites),bootstrap_repeats=1999))
t=pd.DataFrame(rows);order=np.argsort(t.p.to_numpy());rank=np.arange(1,len(t)+1);q=np.minimum.accumulate((t.p.to_numpy()[order]*len(t)/rank)[::-1])[::-1];t['q_BH']=np.nan;t.loc[order,'q_BH']=np.minimum(1,q)
t.to_csv(B/'tables/statistics/future_SSI_case_capture_comparisons.csv',index=False)
print(t.to_string(index=False))

