from pathlib import Path
import pandas as pd,json,hashlib,re
O=Path('work/ssi_inferential_microbiology')
# Flag taxonomy changes before any temporal interpretation.
for fn in ['national_ssi_pathogens.csv','category_enrichment_tests.csv','pooled_category_enrichment_tests.csv','adult_pediatric_pathogen_tests.csv','period_shift_tests.csv','depth_pathogen_tests.csv']:
 d=pd.read_csv(O/fn)
 if 'pathogen' in d:
  d['primary_cross_period_comparability']=~d.pathogen.isin(['Selected Klebsiella spp','Enterobacter spp'])
  d['taxonomy_note']=d.pathogen.map(lambda t:'Klebsiella grouping added K. aerogenes in 2020-2021; Enterobacter grouping changed. Keep period-specific or explicitly qualified.' if t in ['Selected Klebsiella spp','Enterobacter spp'] else 'Explicit source taxon; category membership checked against each source table.')
 d.to_csv(O/fn,index=False)
p=pd.read_csv(O/'national_ssi_pathogens.csv');dp=pd.read_csv(O/'national_ssi_pathogens_by_depth.csv');a=pd.read_csv(O/'national_ssi_amr.csv')
priority=[]
for r in a.itertuples():
 if r.period!='2018-2021' or pd.isna(r.percent_result):continue
 g=p[(p.age==r.age)&(p.period==r.period)&(p.category==r.category)]
 if len(g):n=int(g.total.iloc[0])
 else:
  g=dp[(dp.age==r.age)&(dp.period==r.period)&(dp.depth==r.category)]
  if not len(g):continue
  n=int(g.total.iloc[0])
 priority.append(dict(age=r.age,period=r.period,category=r.category,pathogen=r.pathogen,phenotype=r.phenotype,measure=r.measure,organism_reports=r.reported_count,ssi_pathogen_reports=n,organism_share_percent=100*r.reported_count/n,percent_tested=r.percent_tested,percent_result=r.percent_result,compatible_tested_min=r.compatible_tested_min,compatible_tested_max=r.compatible_tested_max,compatible_result_min=r.compatible_result_min,compatible_result_max=r.compatible_result_max,observed_phenotype_per_100_pathogen_reports_min=100*r.compatible_result_min/n,observed_phenotype_per_100_pathogen_reports_max=100*r.compatible_result_max/n,source_table=r.source_table,count_status='Rounding-compatible range, not a source-published exact count; count only observed tested phenotype, not all true resistance'))
pd.DataFrame(priority).to_csv(O/'amr_occurrence_priority_rounding_bounds.csv',index=False)
# Explicit procedure-to-body-site categories from 2015-2017 adult Table 8 footnotes.
groups={'Abdominal':['Appendix surgery','Bile duct, liver or pancreatic surgery','Liver transplant','Gallbladder surgery','Colon surgery','Gastric surgery','Small bowel surgery','Spleen surgery','Exploratory abdominal surgery (laparotomy)','Rectal surgery'], 'Orthopedic':['Open reduction of fracture','Hip prosthesis','Knee prosthesis','Spinal fusion','Laminectomy'], 'Ob/Gyn':['Cesarean section','Hysterectomy, abdominal','Ovarian surgery','Hysterectomy, vaginal'],'Cardiac':['Cardiac surgery','Heart transplant','Coronary bypass, chest and donor incisions','Coronary bypass, chest incision only','Pacemaker surgery','Thoracic surgery'],'Vascular':['Abdominal aortic aneurysm repair'],'Kidney':['Kidney surgery','Kidney transplant']}
review={'Abdominal':'Review deep/organ-space specimen collection, source-control assessment and procedure-specific prophylaxis delivery with local SSI cultures and AST.','Orthopedic':'Review skin and implant infection prevention, SSI depth classification and local Staphylococcus aureus/MRSA results.','Ob/Gyn':'Review operation-specific prevention delivery and mixed enteric/skin organism findings in local SSI cultures.','Cardiac':'Review skin and device/implant prevention and local Staphylococcus aureus/MRSA surveillance.','Vascular':'Review skin and graft prevention plus local mixed-organism SSI culture results.','Kidney':'Review the local procedure-specific culture record; provided national tables do not supply a dedicated kidney pathogen profile.'}
cross=[]
for cat,procedures in groups.items():
 for proc in procedures:cross.append(dict(california_procedure=proc,national_body_site_category=cat,mapping_source='Adult NHSN 2015-2017 Table 8 footnotes a-g explicitly list these operative procedure categories',source_url='https://pmc.ncbi.nlm.nih.gov/articles/PMC8276252/#T8',linkage_status='Anatomic crosswalk for contextual review only; no patient, isolate, hospital or event linkage to California records',microbiology_review_focus=review[cat],dedicated_2018_2021_pathogen_profile_available=cat!='Kidney'))
assert len(cross)==28
pd.DataFrame(cross).to_csv(O/'california_28_procedure_microbiology_context_crosswalk.csv',index=False)
# Source metadata and local-source checksums.
base=Path('__SOURCE_ROOT__')
sources=[]
for name,path,title,url,tables in [
 ('adult_2015_2017',base/'Conference Bloodstreem Dataset/Sources/CDC_AR/adult_2015_2017.html','Antimicrobial-resistant pathogens associated with adult healthcare-associated infections: Summary of data reported to the National Healthcare Safety Network, 2015-2017','https://pmc.ncbi.nlm.nih.gov/articles/PMC8276252/','Tables 2, 8, 9, 15; Table 8 crosswalk footnotes'),
 ('pediatric_2015_2017',base/'Conference Bloodstreem Dataset/Sources/CDC_AR/pediatric_2015_2017.html','Antimicrobial-resistant pathogens associated with pediatric healthcare-associated infections: Summary of data reported to the National Healthcare Safety Network, 2015-2017','https://pmc.ncbi.nlm.nih.gov/articles/PMC8276251/','Tables 2, 8, 9, 12'),
 ('adult_2018_2021',base/'Survaillance dataset/Sources/CDC_AR/full-hai-pathogens-ar-report/Adult Pathogen & Resistance Tables.pdf','2018-2021 HAI Pathogens & Antimicrobial Resistance Report: Data Tables for Adult HAIs','https://www.cdc.gov/nhsn/hai-report/index.html','Tables 2, 7, 8, 9, 10, 16, 17, 18; PDF pages 3, 9, 10, 12, 13, 21, 23, 25'),
 ('pediatric_2018_2021',base/'Survaillance dataset/Sources/CDC_AR/full-hai-pathogens-ar-report/Pediatric Pathogen & Resistance Tables.pdf','2018-2021 HAI Pathogens & Antimicrobial Resistance Report: Data Tables for Pediatric HAIs','https://www.cdc.gov/nhsn/hai-report/index.html','Tables P2, P6, P7, P10; PDF pages 3, 8, 9, 14'),
 ('methods_2018_2021',base/'Survaillance dataset/Sources/CDC_AR/full-hai-pathogens-ar-report/HAI Pathogen & AR Report 2018-2021.pdf','HAI Pathogens and Antimicrobial Resistance Report, 2018-2021','https://www.cdc.gov/nhsn/hai-report/index.html','Methods: PDF pages 7-9, especially page 8 for taxonomy and phenotype changes')]:
 sources.append(dict(source=name,title=title,local_path=str(path),source_url=url,tables_used=tables,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
pd.DataFrame(sources).to_csv(O/'microbiology_source_metadata.csv',index=False)
# Source-event counts with or without microbiology. Older pediatric exact missing-pathogen count unavailable.
s=pd.read_csv(O/'national_ssi_source_totals.csv');missing={('adult','2015-2017'):27237,('adult','2018-2021'):46099,('pediatric','2018-2021'):1292}
s['ssi_events_without_pathogen']=[missing.get((r.age,r.period),None) for r in s.itertuples()];s['ssi_events_with_pathogen']=s.ssi_events-s.ssi_events_without_pathogen;s['fraction_without_pathogen']=s.ssi_events_without_pathogen/s.ssi_events;s.to_csv(O/'national_ssi_source_totals.csv',index=False)
notes='''SSI MICROBIOLOGY EVIDENCE: SCOPE AND FIGURE QUESTIONS

All inputs were already present in the user-provided local conference directory. No new patient records were created and no national organism profile was attached as an observed California result.

Largest source volume: 378,610 reported SSI pathogens from 330,914 reported SSI events, covering adult and pediatric populations in two nonoverlapping periods. Some SSI events contain no organism, and a single SSI event can contribute up to 3 pathogen reports. These are different denominators. National surveillance may include California events, so these counts cannot be added to California operations or infection counts.

Microbiology Figure 1 question: Are procedure groups characterized by reproducible, distinct pathogen ecologies? Use national_ssi_pathogens.csv as a two-period composition matrix and pooled_category_enrichment_tests.csv for report-share ratio forest plots. Primary findings: adult abdominal E. coli 19.75% vs 7.46% in other surgery groups, share ratio 2.648 (95% CI 2.599-2.699); abdominal Bacteroides 7.27% vs 1.96%, ratio 3.699 (3.565-3.837); abdominal Candida albicans 5.47% vs 1.11%, ratio 4.929 (4.698-5.171); orthopedic S. aureus 35.65% vs 9.88%, ratio 3.610 (3.559-3.661). Each q<0.001. These refer to pathogen-report shares, not postoperative infection risk.

Microbiology Figure 2 question: Does a common adult pathway conceal pediatric pathogen enrichment? Use adult_pediatric_pathogen_tests.csv for paired age contrasts. In 2018-2021, pediatric cardiac S. aureus 171/427 vs adult 2,574/10,506, ratio 1.635 (1.449-1.844), q<0.001. Pediatric orthopedic E. coli 100/892 vs adult 2,883/55,613, ratio 2.163 (1.792-2.610), q<0.001. Pediatric orthopedic P. aeruginosa 100/892 vs adult 3,702/55,613, ratio 1.684 (1.396-2.031), q<0.001.

Microbiology Figure 3 question: Does infection depth identify different diagnostic and prevention review priorities? Use national_ssi_pathogens_by_depth.csv and depth_pathogen_tests.csv. Adult deep-incisional S. aureus 9,563/36,186 vs superficial 11,789/63,988, ratio 1.434 (1.401-1.469), q<0.001. Adult organ/space C. albicans 5,889/115,495 vs superficial 1,383/63,988, ratio 2.359 (2.227-2.499), q<0.001. Organ/space Bacteroides 7,818/115,495 vs 1,781/63,988, ratio 2.432 (2.312-2.558), q<0.001. These are parallel SSI categories, not observed progression from superficial to deep infection.

Microbiology Figure 4 question: Is the distribution of SSI depth shifting toward organ/space reporting? Use national_ssi_depth.csv and depth_period_tests.csv. Adult organ/space proportion of pathogen reports increased from 70,407/154,133 (45.68%) in 2015-2017 to 115,495/215,669 (53.55%) in 2018-2021, ratio 1.172 (1.164-1.180), q<0.001. Orthopedic organ/space share increased from 30.40% to 38.17%, ratio 1.256 (1.232-1.280), q<0.001. Reporting definitions, capture and changing hospital mix may contribute, so do not describe this as within-patient progression or a causal temporal mechanism.

Microbiology Figure 5 question: Does conditional resistance percentage rank procedures differently from the occurrence of resistant phenotypes among reported SSI pathogens? Use national_ssi_amr.csv and amr_occurrence_priority_rounding_bounds.csv. Adult 2018-2021 abdominal MRSA is 52.6% of tested S. aureus, versus orthopedic 36.4%. However S. aureus contributes 6,407/112,285 (5.71%) abdominal vs 18,744/55,613 (33.70%) orthopedic pathogen reports. Rounding-compatible observed MRSA occurrence per 100 SSI pathogen reports is about 2.74 abdominal vs 11.06 orthopedic. This is an evidence-based review priority contrast, not an antibiotic recommendation. Exact tested and resistant counts are not published. Plot published percentages and reconstructed ranges separately; do not label reconstructed values exact. If using P<0.05 stars, source_significant_vs_abdominal comes from the 2015-2017 published mid-P comparisons and must be labeled as source-reported, unadjusted P<0.05, not newly estimated P.

Microbiology Figure 6 question: Where does a hospital alert direct microbiology review? Use california_28_procedure_microbiology_context_crosswalk.csv, explicit 2015-2017 NHSN body-site category definitions, and effect estimates above. This crosswalk translates hospital reporting signals into locally verified culture, AST, prevention-process and source-control review questions. It does not assign national organisms to individual California SSIs, estimate prophylaxis efficacy or select an antimicrobial regimen. The framework can also show the microbiology capture gap: 46,099/190,384 adult SSIs (24.21%) and 1,292/5,054 pediatric SSIs (25.56%) lacked a reported pathogen in 2018-2021. Older adult gap 27,237/132,258 (20.59%). Older pediatric exact gap unavailable.

STATISTICAL INTERPRETATION
Fisher exact tests use published exact pathogen-report marginals. BH correction is applied separately within each named CSV analysis family. Report-share ratios have log-scale 95% CIs; proportion CIs use Wilson. Differences use conservative subtraction of Wilson bounds. These exploratory calculations assume exchangeability of reported pathogens. The published marginals do not identify SSI event IDs or hospital IDs, so within-event co-occurrence and hospital clustering cannot be recovered. P-values support source-level exploratory comparisons and must not be presented as validated California patient-level or hospital-clustered inference. Emphasize magnitude, precision and repetition across sources.

Global composition chi-square tests use common explicitly represented taxa and a reconciled residual within each age-period stratum. Other reported taxa is source-specific and is not analyzed as if it were a fixed biological taxon. No absent organism category is converted to zero.

TAXONOMY AND AMR COMPARABILITY
The 2018-2021 report states that K. aerogenes joins the selected Klebsiella group in 2020-2021, affecting Enterobacter/Klebsiella temporal comparisons. Exclude these two groups from primary like-for-like temporal inference. CRE and extended-spectrum cephalosporin phenotype definitions also changed between reports. Source guidance says MRSA, VRE, MDR P. aeruginosa and carbapenem-NS Acinetobacter definitions are consistent with prior reports. Non-susceptibility is not resistance. All AMR result percentages and tested percentages are published rounded values. Integer compatible bounds and Wilson envelopes assume rounding to the nearest 0.1 percentage point, and are explicitly derived sensitivity quantities rather than published exact denominators.

AMR ROW VALIDATION
2018-2021 adult Table 17 has column order Neurologic, Breast, Vascular. This differs from the pathogen Table 10 order Neurosurgical, Vascular, Breast. The extractor maps both to correct canonical categories and verifies organism report counts against the matching pathogen table for all explicit organisms.
'''
(O/'microbiology_questions_methods_and_findings.txt').write_text(notes)
# Independent checks: consistent report counts across AMR and organism tables wherever exact category counts are exposed.
errors=[];checked=0
for r in a[a.period=='2018-2021'].itertuples():
 g=p[(p.age==r.age)&(p.period==r.period)&(p.category==r.category)&(p.pathogen==r.pathogen)]
 if not len(g):g=dp[(dp.age==r.age)&(dp.period==r.period)&(dp.depth==r.category)&(dp.pathogen==r.pathogen)]
 if len(g):
  checked+=1
  if int(g['count'].iloc[0])!=r.reported_count:errors.append(r._asdict())
assert not errors,errors
# Dash audit of new analytical tables and methods only, excluding verbatim preserved source extracts.
selected=list(O.glob('*tests.csv'))+[O/x for x in ['national_ssi_pathogens.csv','national_ssi_depth.csv','national_ssi_pathogens_by_depth.csv','national_ssi_amr.csv','national_ssi_source_totals.csv','california_28_procedure_microbiology_context_crosswalk.csv','amr_occurrence_priority_rounding_bounds.csv','microbiology_source_metadata.csv','microbiology_questions_methods_and_findings.txt']]
bad=[]
for fn in selected:
 for ch in fn.read_text():
  if ch in '\u2010\u2011\u2012\u2013\u2014\u2015\u2212':bad.append((fn.name,ch))
assert not bad,bad
(O/'additional_validation.json').write_text(json.dumps(dict(amr_organism_count_cells_crosschecked=checked,amr_crosscheck_errors=errors,analysis_ascii_dash_audit=True,california_crosswalk_rows=28,raw_source_counts_reconciled=True),indent=2))
print('Crosschecked',checked,'AMR organism count cells; all agree. All final analytical text passes dash policy.')
# Repetition across disjoint source periods, used as evidence consistency rather than independent hospital validation.
e=pd.read_csv(O/'category_enrichment_tests.csv');early=e[e.period=='2015-2017'];later=e[e.period=='2018-2021'];q=early.merge(later,on=['age','category','pathogen'],suffixes=('_early','_later'))
cols=['age','category','pathogen','report_share_ratio_early','ratio_lower_early','ratio_upper_early','p_value_early','q_value_early','report_share_ratio_later','ratio_lower_later','ratio_upper_later','p_value_later','q_value_later']
q=q[cols].copy();q['same_direction']=(q.report_share_ratio_early>1)==(q.report_share_ratio_later>1);q['both_BH_q_below_005']=(q.q_value_early<.05)&(q.q_value_later<.05);q['taxonomy_stable']=~q.pathogen.isin(['Selected Klebsiella spp','Enterobacter spp']);q.to_csv(O/'cross_period_pathogen_signal_replication.csv',index=False)
