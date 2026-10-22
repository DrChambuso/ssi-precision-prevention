from pathlib import Path
import numpy as np
import pandas as pd
B=Path('__LEGACY_ROOT__')/'outputs/SSI_Prevention_Intelligence/SSI_Inferential_Microbiology_Figures'
# Hospital bootstrap for the absolute five-year difference in signal probabilities.
co=pd.read_csv(B/'reproducibility/maximum_time_to_alert_cohort.csv');ss=sorted(co.site.unique());rng=np.random.default_rng(20261018)
weights=rng.multinomial(len(ss),np.repeat(1/len(ss),len(ss)),size=999)
def km5(g):
 a=[]
 for high in [0,1]:
  z=g[g.high==high];cols=[]
  for time in range(1,6):
   tmp=z[['site','time','event']].copy();tmp['risk']=(tmp.time>=time).astype(int);tmp['events']=((tmp.time==time)&(tmp.event==1)).astype(int)
   vals=tmp.groupby('site')[['risk','events']].sum().reindex(ss,fill_value=0).to_numpy()
   v=weights@vals;rat=np.divide(v[:,1],v[:,0],out=np.zeros(999),where=v[:,0]>0)
   cols.append(1-rat)
  a.append(np.prod(cols,axis=0))
 # Higher minus lower probability of a signal = lower minus higher signal-free probability.
 diff=a[0]-a[1]
 return np.percentile(diff,[2.5,97.5])
d=pd.read_csv(B/'reproducibility/prediction/heldout_predictions.csv');d=d[d['set']=='Test'];top=d[d.year<=2025].groupby('procedure').y.sum().sort_values(ascending=False).index.tolist()
groups=[('All ages and procedures',co),('Adult',co[co.age=='Adult']),('Pediatric',co[co.age=='Pediatric'])]+[(p,co[co.procedure==p])for p in top[:8]]
out=[]
for name,g in groups:
 vals=[]
 for h in [0,1]:
  z=g[g.high==h];sv=1.
  for tm in range(1,6):
   risk=(z.time>=tm).sum();events=((z.time==tm)&(z.event==1)).sum()
   if risk:sv*=1-events/risk
  vals.append(sv)
 lo,up=km5(g);out.append(dict(group=name,units=len(g),five_year_signal_probability_difference=vals[0]-vals[1],lower=lo,upper=up))
pd.DataFrame(out).to_csv(B/'tables/statistics/five_year_signal_probability_differences.csv',index=False)
