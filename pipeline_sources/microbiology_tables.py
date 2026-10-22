from pathlib import Path
import pandas as pd, numpy as np, math, re, json
from statistics import NormalDist
O=Path('work/ssi_inferential_microbiology')
def canon(x):
 x=re.sub(r'[36]$','',x).strip().rstrip('.')
 x=x.replace('Bacteriodes','Bacteroides').replace('Select Klebsiella','Selected Klebsiella')
 if x in ['Other','Other pathogen']:return 'Other reported taxa'
 return x

def parse_count(s):return int(re.match(r'[\d,]+',s)[0].replace(',',''))
rows=[];depth=[];amr=[]
for age in ['adult','pediatric']:
 tables=json.loads((O/f'{age}_tables.json').read_text())
 # 2015-2017 counts
 cats=['All surgery types','Abdominal','Orthopedic','Ob/Gyn','Cardiac'] if age=='adult' else ['All surgery types','Abdominal','Orthopedic','Neurosurgical','Cardiac']
 rr=[r for r in tables['T9']['raw_rows'] if len(r)==7]
 totalrow=[r for r in rr if r[0]['text']=='Total'][0];totals=[parse_count(totalrow[i]['text']) for i in [1,3,4,5,6]]
 for r in rr:
  if r[0]['text'] in ['Total','Pathogen']:continue
  for c,i,n in zip(cats,[1,3,4,5,6],totals):
   rows.append(dict(age=age,period='2015-2017',category=c,pathogen=canon(r[0]['text']),count=parse_count(r[i]['text']),total=n,source_table='Table 9',source_age=age))
 for r in tables['T8']['raw_rows']:
  if len(r)==5 and re.match(r'^[\d,]',r[1]['text']):
   cat=r[0]['text'].replace('Breast surgery','Breast').replace('Prostate surgery','Prostate')
   if cat=='Total':cat='All surgery types'
   n=parse_count(r[4]['text'])
   for dep,i in [('Superficial incisional',1),('Deep incisional',2),('Organ/space',3)]:depth.append(dict(age=age,period='2015-2017',category=cat,depth=dep,count=parse_count(r[i]['text']),total=n,source_table='Table 8'))
 table='T15' if age=='adult' else 'T12'
 for r in tables[table]['raw_rows'][2:]:
  if len(r)!=16:continue
  if r[1]['text']:
   organism=canon(r[0]['text']);organism_counts=[parse_count(r[j]['text']) for j in [1,4,7,10,13]]
  else:
   phenotype=r[0]['text'];measure='resistant' if any(t in phenotype for t in ['MRSA','VRE','CRE']) else 'non-susceptible'
   for c,n,j in zip(cats,organism_counts,[1,4,7,10,13]):
    val=r[j+2]['text'].replace('*','');tested=r[j+1]['text']
    try:pct=float(val)
    except:pct=np.nan
    try:pt=float(tested)
    except:pt=np.nan
    amr.append(dict(age=age,period='2015-2017',category=c,pathogen=organism,phenotype=phenotype,measure=measure,reported_count=n,percent_tested=pt,percent_result=pct,source_significant_vs_abdominal=('*' in r[j+2]['text'] or '*' in r[j+2]['sup']),source_p_threshold=.05 if '*' in r[j+2]['text']+r[j+2]['sup'] else np.nan,source_table='Table '+table[1:]))

def parse_new_pathogens(age,page,cats,first):
 text=(O/f'{age.title()}_2018_2021_page_{page}.txt').read_text();text=text[text.index(first):];text=text[:text.index('Note:')]
 pending=''
 for line in text.splitlines():
  line=line.strip()
  if not line:continue
  m=re.search(r'\s+(\d[\d,]*)(?=\s)',line)
  if not m:pending+=' '+line;continue
  name=canon((pending+' '+line[:m.start()]).strip());pending=''
  nums=line[m.start():].split()
  if name in ['Total','Other reported taxa']:
   counts=[parse_count(nums[2*i]) for i in range(len(cats))]
  else:
   counts=[parse_count(nums[3*i]) for i in range(len(cats))]
  if name=='Total':
   totals=counts
  else:
   for c,x in zip(cats,counts):rows.append(dict(age=age,period='2018-2021',category=c,pathogen=name,count=x,total=None,source_table=f'Table {9 if age=="adult" and page==12 else 10 if age=="adult" and page==13 else 8 if age=="adult" else "P7"}',source_age=age))
 for r in rows:
  if r['age']==age and r['period']=='2018-2021' and r['total'] is None and r['category'] in cats:r['total']=totals[cats.index(r['category'])]

parse_new_pathogens('adult',12,['Abdominal','Orthopedic','Ob/Gyn','Cardiac'],'Escherichia coli')
parse_new_pathogens('adult',13,['Neurosurgical','Vascular','Breast'],'Staphylococcus aureus')
# Adult all-source and depth pathogen rows parsed directly
text=(O/'Adult_2018_2021_page_10.txt').read_text();text=text[text.index('Staphylococcus aureus'):];text=text[:text.index('Total')]
depthpath=[];pending=''
for line in text.splitlines():
 line=line.strip();m=re.search(r'\s+(\d[\d,]*)(?=\s)',line)
 if not line:continue
 if not m:pending+=' '+line;continue
 name=canon((pending+' '+line[:m.start()]).strip());pending='';nums=line[m.start():].split();step=2 if name=='Other reported taxa' else 3
 for i,(dep,n) in enumerate(zip(['All SSI types','Superficial incisional','Deep incisional','Organ/space'],[215669,63988,36186,115495])):
  x=parse_count(nums[step*i]);depthpath.append(dict(age='adult',period='2018-2021',depth=dep,pathogen=name,count=x,total=n,source_table='Table 8'))
  if i==0:rows.append(dict(age='adult',period='2018-2021',category='All surgery types',pathogen=name,count=x,total=n,source_table='Table 8',source_age='adult'))
parse_new_pathogens('pediatric',9,['All surgery types','Abdominal','Orthopedic','Neurosurgical','Cardiac'],'Staphylococcus aureus')
# 2018-2021 SSI depth count tables
for age,page in [('adult',9),('pediatric',8)]:
 text=(O/f'{age.title()}_2018_2021_page_{page}.txt').read_text();text=text[text.index('Abdominal'):];text=text[:text.index('Note:')]
 for line in text.splitlines():
  m=re.search(r'\s+(\d[\d,]*)(?=\s)',line)
  if not m:continue
  cat=line[:m.start()].strip();cat='All surgery types' if cat in ['Total','All surgery types'] else cat
  nums=line[m.start():].split();n=parse_count(nums[0])
  for dep,i in [('Superficial incisional',2),('Deep incisional',4),('Organ/space',6)]:depth.append(dict(age=age,period='2018-2021',category=cat,depth=dep,count=parse_count(nums[i]),total=n,source_table='Table 7' if age=='adult' else 'Table P6'))
# 2018-2021 AMR rows from PDFs, preserve original rounded values and missing suppression
newphenotypes=['Carbapenem-NS','Carbapenem-resistant (CRE)','Extended-spectrum cephalosporin-NS','Cefepime-NS','Vancomycin-resistant (VRE)','Vancomycin-resistant (VRE)','Multidrug-resistant (MDR)','Meth/ox/cefox - resistant (MRSA)']
for age,page,cats,table in [('adult',21,['Abdominal','Orthopedic','Ob/Gyn','Cardiac'],'Table 16'),('adult',23,['Neurosurgical','Breast','Vascular'],'Table 17'),('adult',25,['Superficial incisional','Deep incisional','Organ/space'],'Table 18'),('pediatric',14,['All surgery types','Abdominal','Orthopedic','Neurosurgical','Cardiac'],'Table P10')]:
 text=(O/f'{age.title()}_2018_2021_page_{page}.txt').read_text();text=text[text.index('Acinetobacter spp.'):];text=text[:text.index('Refer to Technical') if 'Refer to Technical' in text else text.index('Note:')]
 lines=[x.strip() for x in text.splitlines() if x.strip()];i=0;ph=0
 while i<len(lines):
  line=lines[i]
  if not any(line.startswith(x) for x in ['Acinetobacter spp.','Select Enterobacterales','Enterobacter spp.','Enterococcus faecalis','Enterococcus faecium','Pseudomonas aeruginosa','Staphylococcus aureus']):i+=1;continue
  m=re.search(r'\s+(\d[\d,]*)(?=\s|$)',line);name=canon(re.sub(r'\d+$','',line[:m.start()]).strip());counts=[int(x.replace(',','')) for x in line[m.start():].split()]
  nxt=lines[i+1];phenotype=newphenotypes[ph];ph+=1
  assert nxt.startswith(phenotype),(age,page,nxt,phenotype)
  values=nxt[len(phenotype):].split();assert len(values)==2*len(cats),(age,page,name,values)
  for j,(cat,n) in enumerate(zip(cats,counts)):
   pt=float(values[2*j]) if values[2*j]!='.' else np.nan;pct=float(values[2*j+1]) if values[2*j+1]!='.' else np.nan
   amr.append(dict(age=age,period='2018-2021',category=cat,pathogen=name,phenotype=phenotype,measure='non-susceptible' if phenotype.endswith('-NS') else 'resistant',reported_count=n,percent_tested=pt,percent_result=pct,source_significant_vs_abdominal=False,source_p_threshold=np.nan,source_table=table))
  i+=2

p=pd.DataFrame(rows);p['count']=p['count'].astype(int);p['total']=p['total'].astype(int);p['proportion']=p['count']/p['total']
d=pd.DataFrame(depth);d['proportion']=d['count']/d['total'];dp=pd.DataFrame(depthpath);dp['proportion']=dp['count']/dp['total']
a=pd.DataFrame(amr)
# Rounding-compatible counts are derived bounds, not published exact tested counts.
def compatible(N,pt,pr):
 if pd.isna(pt) or pd.isna(pr):return (np.nan,)*7
 ns=range(max(1,math.ceil(N*(pt-.05)/100-1e-9)), min(N,math.ceil(N*(pt+.05)/100-1e-9)-1)+1)
 possibilities=[]
 for n in ns:
  low=max(0,math.ceil(n*(pr-.05)/100-1e-9));high=min(n,math.ceil(n*(pr+.05)/100-1e-9)-1)
  if low<=high:
   for k in range(low,high+1):possibilities.append((n,k))
 if not possibilities:return (np.nan,)*7
 lows=[];his=[]
 for n,k in possibilities:
  z=1.959963984540054;v=k/n;den=1+z*z/n;ctr=(v+z*z/(2*n))/den;half=z*math.sqrt(v*(1-v)/n+z*z/(4*n*n))/den;lows.append(ctr-half);his.append(ctr+half)
 return min(n for n,k in possibilities),max(n for n,k in possibilities),min(k for n,k in possibilities),max(k for n,k in possibilities),min(lows),max(his),len(possibilities)
a[['compatible_tested_min','compatible_tested_max','compatible_result_min','compatible_result_max','rounding_aware_wilson_lower','rounding_aware_wilson_upper','compatible_integer_pairs']]=pd.DataFrame([compatible(int(r.reported_count),r.percent_tested,r.percent_result) for r in a.itertuples()])
a['count_status']='Reported organism count plus rounded percentages; integer ranges reconstructed under nearest 0.1 percentage-point rounding'
a['exact_tested_count_available']=False
# Checks preserve source population and categories
assert not p.duplicated(['age','period','category','pathogen']).any()
for k,g in p.groupby(['age','period','category']):assert g['count'].sum()==g['total'].iloc[0],(k,g['count'].sum(),g['total'].iloc[0])
for k,g in d.groupby(['age','period','category']):assert g['count'].sum()==g['total'].iloc[0],k
for k,g in dp.groupby(['age','period','depth']):assert g['count'].sum()==g['total'].iloc[0],k
p.to_csv(O/'national_ssi_pathogens.csv',index=False);d.to_csv(O/'national_ssi_depth.csv',index=False);dp.to_csv(O/'national_ssi_pathogens_by_depth.csv',index=False);a.to_csv(O/'national_ssi_amr.csv',index=False)
# Count-based exploratory report-level comparisons. No patient/hospital clustering available for these published marginals.
def wilson(k,n):
 z=NormalDist().inv_cdf(.975);q=k/n;den=1+z*z/n;ctr=(q+z*z/(2*n))/den;half=z*math.sqrt(q*(1-q)/n+z*z/(4*n*n))/den;return ctr-half,ctr+half

def compare(k1,n1,k0,n0):
 pv=np.nan;l1,u1=wilson(k1,n1);l0,u0=wilson(k0,n0)
 correction=any(x==0 for x in [k1,n1-k1,k0,n0-k0]);c=.5 if correction else 0
 x1=k1+c;x0=k0+c;N1=n1+2*c;N0=n0+2*c;rr=(x1/N1)/(x0/N0);se=math.sqrt(1/x1-1/N1+1/x0-1/N0)
 return dict(count1=k1,total1=n1,count0=k0,total0=n0,share1=k1/n1,share0=k0/n0,share1_lower=l1,share1_upper=u1,share0_lower=l0,share0_upper=u0,report_share_ratio=rr,ratio_lower=math.exp(math.log(rr)-1.96*se),ratio_upper=math.exp(math.log(rr)+1.96*se),difference_percentage_points=100*(k1/n1-k0/n0),difference_lower=100*(l1-u0),difference_upper=100*(u1-l0),p_value=max(pv,1e-300),p_underflow=pv==0,zero_cell_correction=correction,test='Fisher exact, report-level exploratory',ci='Wilson proportion; log-ratio; conservative difference of Wilson bounds')
def bh(df):
 if len(df)==0:return df
 pv=df['p_value'].to_numpy();o=np.argsort(pv);qq=np.minimum.accumulate((pv[o]*len(df)/np.arange(1,len(df)+1))[::-1])[::-1];q=np.empty(len(df));q[o]=np.minimum(qq,1);df['q_value']=q;return df
# category enrichment vs all other surgical categories within each source period
res=[]
for r in p[p.category!='All surgery types'].itertuples():
 allr=p[(p.age==r.age)&(p.period==r.period)&(p.category=='All surgery types')&(p.pathogen==r.pathogen)]
 if len(allr)!=1 or r.pathogen=='Other reported taxa':continue
 ar=allr.iloc[0];res.append(dict(age=r.age,period=r.period,category=r.category,pathogen=r.pathogen,comparison='Specified surgical category vs all other surgical categories',**compare(r.count,r.total,int(ar['count']-r.count),int(ar['total']-r.total))))
bh(pd.DataFrame(res)).to_csv(O/'category_enrichment_tests.csv',index=False)
# pooled period enrichment maximizes exact counted volume, only taxa present in both periods' category and all-source totals
res=[]
for (age,cat,tax),g in p[p.category!='All surgery types'].groupby(['age','category','pathogen']):
 if set(g.period)!={'2015-2017','2018-2021'} or tax=='Other reported taxa':continue
 ag=p[(p.age==age)&(p.category=='All surgery types')&(p.pathogen==tax)]
 if len(ag)!=2:continue
 n1=int(g.total.sum());k1=int(g['count'].sum());nall=int(ag.total.sum());kall=int(ag['count'].sum())
 res.append(dict(age=age,period='2015-2021 pooled nonoverlapping periods',category=cat,pathogen=tax,comparison='Specified surgical category vs all other surgical categories',**compare(k1,n1,kall-k1,nall-n1)))
bh(pd.DataFrame(res)).to_csv(O/'pooled_category_enrichment_tests.csv',index=False)
# adult-pediatric organism share comparisons, same source period/category
res=[]
for (period,cat,tax),g in p.groupby(['period','category','pathogen']):
 if set(g.age)!={'adult','pediatric'} or tax=='Other reported taxa':continue
 x=g[g.age=='pediatric'].iloc[0];y=g[g.age=='adult'].iloc[0]
 res.append(dict(period=period,category=cat,pathogen=tax,comparison='Pediatric vs adult pathogen report share',**compare(int(x['count']),int(x.total),int(y['count']),int(y.total))))
bh(pd.DataFrame(res)).to_csv(O/'adult_pediatric_pathogen_tests.csv',index=False)
# later vs earlier shares, same age/category
res=[]
for (age,cat,tax),g in p.groupby(['age','category','pathogen']):
 if set(g.period)!={'2015-2017','2018-2021'} or tax=='Other reported taxa':continue
 x=g[g.period=='2018-2021'].iloc[0];y=g[g.period=='2015-2017'].iloc[0]
 res.append(dict(age=age,category=cat,pathogen=tax,comparison='2018-2021 vs 2015-2017 pathogen report share',**compare(int(x['count']),int(x.total),int(y['count']),int(y.total))))
bh(pd.DataFrame(res)).to_csv(O/'period_shift_tests.csv',index=False)
# pathogen deep and organ/space vs superficial
res=[]
for tax,g in dp.groupby('pathogen'):
 if tax=='Other reported taxa':continue
 for dep in ['Deep incisional','Organ/space']:
  x=g[g.depth==dep].iloc[0];y=g[g.depth=='Superficial incisional'].iloc[0]
  res.append(dict(age='adult',period='2018-2021',pathogen=tax,depth=dep,comparison=dep+' vs superficial incisional',**compare(int(x['count']),int(x.total),int(y['count']),int(y.total))))
bh(pd.DataFrame(res)).to_csv(O/'depth_pathogen_tests.csv',index=False)
# case depth report share by procedure, adult and pediatric difference; period shifts
res=[]
for (period,cat,dep),g in d.groupby(['period','category','depth']):
 if set(g.age)!={'adult','pediatric'}:continue
 x=g[g.age=='pediatric'].iloc[0];y=g[g.age=='adult'].iloc[0]
 res.append(dict(period=period,category=cat,depth=dep,comparison='Pediatric vs adult SSI-depth report share',**compare(int(x['count']),int(x.total),int(y['count']),int(y.total))))
bh(pd.DataFrame(res)).to_csv(O/'depth_age_tests.csv',index=False)
res=[]
for (age,cat,dep),g in d.groupby(['age','category','depth']):
 if set(g.period)!={'2015-2017','2018-2021'}:continue
 x=g[g.period=='2018-2021'].iloc[0];y=g[g.period=='2015-2017'].iloc[0]
 res.append(dict(age=age,category=cat,depth=dep,comparison='2018-2021 vs 2015-2017 SSI-depth report share',**compare(int(x['count']),int(x.total),int(y['count']),int(y.total))))
bh(pd.DataFrame(res)).to_csv(O/'depth_period_tests.csv',index=False)
# global exact-source composition chi-square tests on reconciled mutually exclusive taxa
res=[]
for (age,period),g in p.groupby(['age','period']):
 cats=[c for c in ['Abdominal','Orthopedic','Ob/Gyn','Cardiac','Neurosurgical','Vascular','Breast'] if c in set(g.category)]
 # Use only shared explicitly represented taxa, put all remaining taxa in common residual.
 sets=[set(g[g.category==c].pathogen)-{'Other reported taxa'} for c in cats];common=sorted(set.intersection(*sets));matrix=[]
 for c in cats:
  z=g[g.category==c].set_index('pathogen');vv=[int(z.loc[t,'count']) for t in common];vv.append(int(z.total.iloc[0])-sum(vv));matrix.append(vv)
 mat=np.array(matrix);ex=np.outer(mat.sum(axis=1),mat.sum(axis=0))/mat.sum();stat=float(((mat-ex)**2/ex).sum());dof=(mat.shape[0]-1)*(mat.shape[1]-1);pval=np.nan
 res.append(dict(age=age,period=period,n_reports=sum(sum(x) for x in matrix),categories=len(cats),explicit_taxa=len(common),chi_square=stat,degrees_freedom=dof,p_value=max(pval,1e-300),minimum_expected=float(ex.min()),cramers_v=math.sqrt(stat/(sum(sum(x) for x in matrix)*min(len(cats)-1,len(common)))),test='Pearson chi-square on shared explicit taxa plus common residual'))
pd.DataFrame(res).to_csv(O/'global_composition_tests.csv',index=False)
source=pd.DataFrame([dict(age='adult',period='2015-2017',ssi_events=132258,pathogen_reports=154133),dict(age='adult',period='2018-2021',ssi_events=190384,pathogen_reports=215669),dict(age='pediatric',period='2015-2017',ssi_events=3218,pathogen_reports=3526),dict(age='pediatric',period='2018-2021',ssi_events=5054,pathogen_reports=5282)])
source.to_csv(O/'national_ssi_source_totals.csv',index=False)
summary=dict(national_ssi_pathogen_reports=int(source.pathogen_reports.sum()),national_ssi_events=int(source.ssi_events.sum()),pathogen_rows=len(p),depth_rows=len(d),amr_rows=len(a),amr_source_p_markers=int(a.source_significant_vs_abdominal.sum()),amr_exact_tested_counts=0,amr_rounding_compatible_cells=int(a.compatible_tested_min.notna().sum()),original_bloodstream_source_volume=274807,california_linkage='No row-level hospital, patient, procedure or event identifiers linking microbiology to California SSI reports; national SSI surveillance can overlap California cases, so denominators must not be added',note='Pathogen report counts are not operation or patient counts. Fisher tests assume report exchangeability and lack hospital or event clustering because only published marginals are available. Periods are nonoverlapping but facilities can recur. Treat count-based microbiology p-values as exploratory, and emphasize effect sizes, Wilson CIs, replication, BH correction. AMR count ranges are reconstructed under nearest0.1 percentage-point rounding, never presented as source exact counts.')
(O/'microbiology_inventory_and_validation.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2));print(pd.read_csv(O/'global_composition_tests.csv').to_string(index=False))
