from pathlib import Path
import pandas as pd, json, hashlib
S=Path('outputs/SSI_Prevention_Intelligence/SSI_Integrated_Publication_Revision/tables/microbiology')
O=Path('work/ssi_figure17_redesign/fourpanel_analysis')
p=pd.read_csv(S/'national_ssi_pathogens.csv');d=pd.read_csv(S/'national_ssi_depth.csv');a=pd.read_csv(S/'national_ssi_amr.csv')
# Stable explicit taxa present in every source-defined profile. 'Other' is reconstructed from the full source total.
explicit=[]
for (age,period,cat),g in p[p.category!='All surgery types'].groupby(['age','period','category']):
 explicit.append(set(g.pathogen)-{'Other reported taxa','Selected Klebsiella spp','Enterobacter spp'})
taxa=sorted(set.intersection(*explicit));assert len(taxa)==8,taxa
rows=[];counts=[];depths=[];amr=[]
for (age,period),g in p.groupby(['age','period']):
 cats=sorted(set(g.category)-{'All surgery types'})
 allg=g[g.category=='All surgery types'].set_index('pathogen');total=int(allg.total.iloc[0]);known_total=0;known_counts={t:0 for t in taxa};known_depths={dep:0 for dep in ['Superficial incisional','Deep incisional','Organ/space']}
 for cat in cats+['Other procedures']:
  if cat!='Other procedures':
   gg=g[g.category==cat].set_index('pathogen');N=int(gg.total.iloc[0]);kk={t:int(gg.loc[t,'count']) for t in taxa};known_total+=N
   for t in taxa:known_counts[t]+=kk[t]
   dd=d[(d.age==age)&(d.period==period)&(d.category==cat)].set_index('depth');dd={dep:int(dd.loc[dep,'count']) for dep in known_depths}
   for dep in known_depths:known_depths[dep]+=dd[dep]
  else:
   N=total-known_total;kk={t:int(allg.loc[t,'count'])-known_counts[t] for t in taxa}
   dd0=d[(d.age==age)&(d.period==period)&(d.category=='All surgery types')].set_index('depth');dd={dep:int(dd0.loc[dep,'count'])-known_depths[dep] for dep in known_depths}
  assert N>0 and min(kk.values())>=0 and min(dd.values())>=0 and sum(dd.values())==N
  kk['Remaining reported taxa']=N-sum(kk.values());assert kk['Remaining reported taxa']>=0
  key=age+'|'+period+'|'+cat
  rows.append(dict(profile_id=key,age=age,period=period,category=cat,n_pathogen_reports=N,role='Discovery' if period=='2015-2017' else 'Later evaluation',residual_profile=cat=='Other procedures'))
  for t,k in kk.items():counts.append(dict(profile_id=key,pathogen=t,count=k,total=N,proportion=k/N))
  for dep,k in dd.items():depths.append(dict(profile_id=key,depth=dep,count=k,total=N,proportion=k/N))
  aa=a[(a.age==age)&(a.period==period)&(a.category==cat)&(a.pathogen=='Staphylococcus aureus')&a.phenotype.str.contains('MRSA',na=False)]
  if period=='2018-2021' and len(aa)==1:
   ar=aa.iloc[0];amr.append(dict(profile_id=key,age=age,category=cat,percent_mrsa=float(ar.percent_result),percent_tested=float(ar.percent_tested),reported_s_aureus=int(ar.reported_count),compatible_tested_min=int(ar.compatible_tested_min),compatible_tested_max=int(ar.compatible_tested_max),compatible_mrsa_min=int(ar.compatible_result_min),compatible_mrsa_max=int(ar.compatible_result_max),n_ssi_pathogen_reports=N,source_table=ar.source_table))
profiles=pd.DataFrame(rows);C=pd.DataFrame(counts);D=pd.DataFrame(depths);A=pd.DataFrame(amr)
assert profiles.n_pathogen_reports.sum()==378610
assert profiles[profiles.role=='Discovery'].n_pathogen_reports.sum()==157659
assert profiles[profiles.role=='Later evaluation'].n_pathogen_reports.sum()==220951
profiles.to_csv(O/'profile_metadata.csv',index=False);C.to_csv(O/'profile_counts_long.csv',index=False);D.to_csv(O/'profile_depth_counts_long.csv',index=False);A.to_csv(O/'later_conditional_mrsa_profiles.csv',index=False)
wide=C.pivot(index='profile_id',columns='pathogen',values='count').reset_index();wide.to_csv(O/'profile_counts_wide.csv',index=False)
source=[dict(file=f.name,sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in [S/'national_ssi_pathogens.csv',S/'national_ssi_depth.csv',S/'national_ssi_amr.csv']]
(O/'source_validation.json').write_text(json.dumps(dict(stable_explicit_taxa=taxa,composition_components=len(taxa)+1,profile_count=len(profiles),discovery_profiles=int((profiles.role=='Discovery').sum()),evaluation_profiles=int((profiles.role=='Later evaluation').sum()),all_pathogen_reports=int(profiles.n_pathogen_reports.sum()),later_mrsa_profiles=len(A),later_mrsa_pathogen_reports=int(A.n_ssi_pathogen_reports.sum()),later_mrsa_s_aureus_reports=int(A.reported_s_aureus.sum()),all_compositions_close=True,all_depth_rows_close=True,unreported_taxa_imputed_zero=False,taxonomy_shift_groups_excluded_as_explicit_features=True,source_files=source),indent=2))
print(json.dumps(json.loads((O/'source_validation.json').read_text()),indent=2))
