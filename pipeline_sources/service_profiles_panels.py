from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd

ROOT=Path('__LEGACY_ROOT__')
O=ROOT/'work/ssi_figure17_redesign/fourpanel_prediction_analysis'
source=ROOT/'work/ssi_new_prediction/lagged_prediction_cohort.csv.gz'
train=pd.read_csv(O/'training_profile_assignments.csv')
test=pd.read_csv(O/'later_test_profile_assignments.csv')
population=pd.read_csv(O/'profile_population_and_outcomes.csv')
centers=pd.read_csv(O/'frozen_training_centroids.csv')
variance=pd.read_csv(O/'PCA_training_explained_variance.csv')
loadings=pd.read_csv(O/'PCA_training_loadings.csv')
contrasts=pd.read_csv(O/'profile_future_outcome_pairwise_contrasts.csv')
global_tests=pd.read_csv(O/'profile_future_outcome_global_tests.csv')
names={1:'Lower-volume reports',2:'Higher volume, lower SSI history',3:'Higher volume, higher SSI history'}

sites=sorted(test.site.unique());B=1999;rng=np.random.default_rng(20261021)
weights=rng.multinomial(len(sites),np.repeat(1/len(sites),len(sites)),size=B)
rows=[]
for k,g in test.groupby('profile'):
    h=g.groupby('site').agg(reports=('outcome','size'),signals=('outcome','sum'),operations=('n','sum'),SSI_cases=('y','sum'),SSI_positive_reports=('any_SSI','sum')).reindex(sites,fill_value=0)
    values=weights@h.to_numpy()
    boot={'signal_fraction':values[:,1]/values[:,0],
          'SSI_rate_per_1000':1000*values[:,3]/values[:,2],
          'SSI_positive_report_fraction':values[:,4]/values[:,0]}
    point={'signal_fraction':g.outcome.mean(),'SSI_rate_per_1000':1000*g.y.sum()/g.n.sum(),'SSI_positive_report_fraction':g.any_SSI.mean()}
    row={'profile':int(k),'label':names[k],'reports':len(g),'sites':g.site.nunique(),'units':g.unit.nunique(),
         'operations':int(g.n.sum()),'SSI_cases':int(g.y.sum()),'signals':int(g.outcome.sum()),'SSI_positive_reports':int(g.any_SSI.sum()),
         'share_of_test_reports':len(g)/len(test),'share_of_test_operations':g.n.sum()/test.n.sum(),
         'share_of_test_SSI_cases':g.y.sum()/test.y.sum(),'share_of_test_signals':g.outcome.sum()/test.outcome.sum(),
         'bootstrap_repeats':B,'bootstrap_frame_sites':len(sites)}
    for metric,draws in boot.items():
        lo,hi=np.quantile(draws,[.025,.975]);row[metric]=point[metric];row[metric+'_lower']=lo;row[metric+'_upper']=hi
    rows.append(row)
summary=pd.DataFrame(rows);summary.to_csv(O/'panel_b_prevalence_and_all_profile_outcomes.csv',index=False)

# Re-express the same three pairwise tests using Profile 2 as the practical reference.
reference=[]
for row in contrasts.to_dict('records'):
    if row['comparison']=='Profile 2 versus Profile 1':
        row['comparison']='Profile 1 versus Profile 2'
        row['effect'],row['lower'],row['upper']=1/row['effect'],1/row['upper'],1/row['lower']
    reference.append(row)
reference=pd.DataFrame(reference);reference.to_csv(O/'profile_future_contrasts_reference_profile2.csv',index=False)

# Descriptive training procedure mix, selected by report count without outcomes.
proc=[]
for dataset,frame in [('Training',train),('Test',test)]:
    for k,g in frame.groupby('profile'):
        for procedure in sorted(frame.procedure.unique()):
            n=int((g.procedure==procedure).sum())
            proc.append({'dataset':dataset,'profile':int(k),'procedure':procedure,'reports':n,'profile_reports':len(g),'fraction':n/len(g)})
proc=pd.DataFrame(proc);proc.to_csv(O/'training_and_test_procedure_mix_descriptive.csv',index=False)
training=proc[proc.dataset=='Training']
selected=set()
for k,g in training.groupby('profile'):
    selected.update(g.sort_values(['reports','procedure'],ascending=[False,True]).head(3).procedure)
selected=sorted(selected)
labels={'log_volume':'Prior operation volume',
        'log_expected_rate':'Smoothed prior expected-rate feature',
        'log_prior_sir':'Prior observed/predicted SSI ratio',
        'log_history_sir':'Three-year observed/predicted SSI ratio'}
heat=[]
for feature in labels:
    v=centers.set_index('profile')[feature].reindex([1,2,3]).to_numpy()
    z=(v-v.mean())/v.std(ddof=1)
    for j,k in enumerate([1,2,3]):
        heat.append({'block':'Prior features','row':labels[feature],'profile':k,
                     'raw_value':v[j],'raw_unit':'Training-standardized feature mean',
                     'row_standardized_value':z[j],'reports':int((train.profile==k).sum())})
for procedure in selected:
    a=training[training.procedure==procedure].set_index('profile').reindex([1,2,3]);v=a.fraction.to_numpy()
    z=(v-v.mean())/v.std(ddof=1)
    for j,k in enumerate([1,2,3]):
        heat.append({'block':'Training procedure mix','row':procedure,'profile':k,
                     'raw_value':v[j],'raw_unit':'Fraction of training reports in profile',
                     'row_standardized_value':z[j],'reports':int(a.loc[k,'reports'])})
heat=pd.DataFrame(heat);heat.to_csv(O/'panel_c_training_components_and_procedure_mix.csv',index=False)
pd.DataFrame({'procedure':selected}).to_csv(O/'panel_c_union_top3_procedures.csv',index=False)

# Report-level future incidence distribution for the two similar-volume history profiles.
box=test[test.profile.isin([2,3])][['unit','site','age','procedure','year','profile','n','y','e','outcome','SSI_rate_per_1000','log1p_SSI_rate_per_1000']].copy()
assert len(box)==11502
box.to_csv(O/'panel_d_all_11502_report_rates.csv',index=False)
box_summaries=[]
for k,g in box.groupby('profile'):
    for field in ['SSI_rate_per_1000','log1p_SSI_rate_per_1000']:
        qs=np.quantile(g[field],[0,.25,.5,.75,1]);iqr=qs[3]-qs[1]
        within=g.loc[g[field].between(qs[1]-1.5*iqr,qs[3]+1.5*iqr),field]
        box_summaries.append({'profile':int(k),'measure':field,'reports':len(g),'minimum':qs[0],
            'Q1':qs[1],'median':qs[2],'Q3':qs[3],'maximum':qs[4],
            'lower_Tukey_whisker':within.min(),'upper_Tukey_whisker':within.max(),
            'zero_SSI_reports':int((g.y==0).sum()),'operations':int(g.n.sum()),'SSI_cases':int(g.y.sum())})
box_summaries=pd.DataFrame(box_summaries);box_summaries.to_csv(O/'panel_d_boxplot_summary.csv',index=False)

def rec(frame):return json.loads(frame.to_json(orient='records',double_precision=15))
model_descriptions={'future_signal_adjusted_RR':'Modified-Poisson future annual signal, adjusted for age, procedure and target year.',
 'future_SSI_incidence_adjusted_IRR':'Poisson future SSI count with log(current operations) offset, adjusted for age, procedure and target year.',
 'future_signal_volume_expected_rate_sensitivity_RR':'As primary signal model, additionally adjusted for prior log-volume and smoothed prior expected-rate feature.',
 'future_incidence_volume_expected_rate_sensitivity_IRR':'As primary incidence model, additionally adjusted for prior log-volume and smoothed prior expected-rate feature.'}
metadata={'title':'Earlier report profiles identify distinct later SSI reporting and incidence patterns',
 'question':'Can three operational profiles defined without target outcomes distinguish later annual SSI signals and actual SSI incidence?',
 'design':'Exploratory K=3 unsupervised training on prior-only report features, frozen before later-year assignment and outcome evaluation.',
 'training_reports':len(train),'training_sites':train.site.nunique(),'training_years':[2017,2022],
 'test_reports':len(test),'test_sites':test.site.nunique(),'test_years':[2023,2025],
 'test_operations':int(test.n.sum()),'test_SSI_cases':int(test.y.sum()),'test_signals':int(test.outcome.sum()),
 'training_test_site_overlap':len(set(train.site)&set(test.site)),
 'training_test_unit_overlap':len(set(train.unit)&set(test.unit)),
 'bootstrap_replicates':1999,'bootstrap_seed':20261021,'cluster_unit':'Canonical named hospital site, retaining all report years, age groups and procedures.',
 'profile_labels':names,
 'profile_definition':{'method':'K-means Euclidean clustering of four training-standardized prior-only continuous features.',
  'k':3,'random_seed':20261019,'random_starts':100,'maximum_iterations':100,
  'labels':'Increasing training-centroid prior log-volume; future outcomes were not used to order profile labels.',
  'assignment':'Nearest frozen training centroid using squared Euclidean distance and training-only means/SDs.',
  'features':['log(1+prior operations)','log((prior predicted SSI+0.5)/(prior operations+1))','log((prior observed SSI+0.5)/(prior predicted SSI+0.5))','log((available t-3 to t-1 observed SSI sum+0.5)/(available predicted SSI sum+0.5))'],
  'unit':'An annual report profile, not an immutable hospital type; the same service can change profile across years.'},
 'PCA':{'fit':'Training-standardized features only; test points projected with frozen training loadings.',
   'PC1_variance_fraction':float(variance.variance_fraction.iloc[0]),'PC2_variance_fraction':float(variance.variance_fraction.iloc[1]),
   'PC1_PC2_variance_fraction':float(variance.variance_fraction.iloc[:2].sum()),'variance':rec(variance),'loadings':rec(loadings)},
 'panels':{
  'a':{'title':'Frozen report profiles in later years','data_file':'later_test_profile_assignments.csv','point_count':len(test),
    'x':'PC1','y':'PC2','group':'profile','hulls_file':'all_test_points_convex_hulls.csv',
    'hull_definition':'Convex hull of all test points assigned to each profile; descriptive projection footprint, not a confidence region.',
    'alternative_display_sample':'optional_PCA_display_sample_3000.csv contains 1,000 random test points per profile, seed 20261020. If used, label it 3,000 displayed of 18,132 analyzed. All-point plotting is preferred when legible.',
    'inference':'No P value on PCA separation or clustering geometry; those are constructed from the features.'},
  'b':{'title':'Following-report signal prevalence','data_file':'panel_b_prevalence_and_all_profile_outcomes.csv',
    'height':'signal_fraction','lower':'signal_fraction_lower','upper':'signal_fraction_upper',
    'CI':'1999 common whole-hospital percentile bootstrap draws.',
    'counts':'signals/reports',
    'pairwise_model':'future_signal_adjusted_RR','global_tests':rec(global_tests[global_tests.model=='future_signal_adjusted_RR']),
    'contrasts':rec(reference[reference.model=='future_signal_adjusted_RR']),
    'primary_contrast':'Profile 3 versus Profile 2, whose volume and expected-rate centroids are similar.'},
  'c':{'title':'Prior components and operative mix','data_file':'panel_c_training_components_and_procedure_mix.csv',
    'feature_definition':'Four frozen training-center means on the training-z scale.',
    'procedure_selection':'Union of top three operative procedures by number of training reports within each profile, with no outcomes used for selection.',
    'procedure_list':selected,'procedure_shares':'Count of training reports for procedure/profile divided by all training reports in that profile.',
    'color':'Row-standardized values across the three profiles, descriptive; exact feature values and procedure shares are provided separately.',
    'inference':'No P values for defining components or procedure composition.'},
  'd':{'title':'Future observed SSI rates in similar-volume profiles','data_file':'panel_d_all_11502_report_rates.csv',
    'reports':len(box),'displayed_reports':len(box),'model_reports':len(test),'model_hospitals':int(test.site.nunique()),
    'displayed_hospitals':int(box.site.nunique()),'displayed_operations':int(box.n.sum()),'displayed_SSI_cases':int(box.y.sum()),
    'groups':[2,3],'box_summary_file':'panel_d_boxplot_summary.csv',
    'point_grain':'One observed annual report. Every zero-SSI report is retained.',
    'y':'log1p_SSI_rate_per_1000','suggested_axis_label':'SSIs per 1,000 operations (log[1+rate] scale)',
    'box_definition':'Median and interquartile range; Tukey 1.5 IQR whiskers of the displayed transformed report rates.',
    'tick_suggestion_original_rates':[0,1,5,10,25,50,100,500,1000],
    'test':'Exposure-offset Poisson count model, age/procedure/year adjusted, hospital-cluster robust inference. No Mann-Whitney test.',
    'contrast':rec(reference[(reference.model=='future_SSI_incidence_adjusted_IRR')&(reference.comparison=='Profile 3 versus Profile 2')]),
    'descriptive_note':'Displayed distributions use all 11,502 Profile 2/3 reports, including zeros. The IRR uses the full 18,132-report adjusted model to retain all available information. It compares count-based SSI incidence using operation exposures, rather than report medians.'}},
 'population_table':rec(summary),'training_and_test_population_table':rec(population),
 'frozen_centroids':rec(centers),'model_descriptions':model_descriptions,
 'sensitivity_contrasts':rec(reference[reference.model.str.contains('sensitivity')]),
 'cautions':['K=3 is an exploratory visualization choice, not a validated optimum selected by clinical utility.',
  'Profiles characterize prior reporting features; they are not microbial ecotypes, patient-level disease states or causal mechanisms.',
  'Training and test hospitals overlap. The evaluation is chronological later-report testing, not an independent-hospital validation.',
  'Uncertainty is conditional on the frozen training profile definition and does not incorporate re-estimation of clusters.',
  'Component and procedure heatmaps are descriptive; testing their separation would be circular.',
  'The smoothed expected-rate feature contains a half-count constant and is not the unsmoothed source expected SSI rate.',
  'This summarizes prognostic patterns. Incremental predictive utility versus the already fitted full signal model has not been established.',
  'Keep report observations, operation exposure denominators, and SSI case counts distinct.'],
 'source_path':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'reproducibility_scripts':['fit_frozen_report_profiles.R','prepare_fourpanel_data.py','verify_fourpanel_data.py']}

def clean(x):
    if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
    if isinstance(x,list):return [clean(v) for v in x]
    if isinstance(x,(np.integer,)):return int(x)
    if isinstance(x,(np.floating,)):return float(x)
    return x
metadata=clean(metadata)
js=json.dumps(metadata,indent=2,ensure_ascii=True,allow_nan=False)+'\n'
assert js.isascii();(O/'fourpanel_analysis.json').write_text(js)
notes=['CALIFORNIA FOUR-PANEL FROZEN REPORT-PROFILE OPTION',metadata['question'],
 'All 39,353 training reports and 18,132 later-year test reports are used. Four prior-only features define three exploratory frozen profiles. No target outcomes enter clustering or PCA.',
 'Suggested layout: a training-fitted PCA projection of all 18,132 later test reports with descriptive convex hulls; b future report-signal prevalence with 1,999 hospital-bootstrap intervals, global/pairwise adjusted RR tests; c frozen feature components and training procedure mix; d report-level future SSI-rate box/jitter for Profiles 2 and 3 (11,502 reports), with exposure-offset hospital-robust Poisson IRR from the full 18,132-report model.',
 'Main comparison: higher-volume lower-history Profile 2 versus similar-volume higher-history Profile 3. Profile 1 is lower-volume reporting and should not be labeled low clinical risk.',
 'No P values belong on defining feature components, cluster geometry, or procedure mix. No Mann-Whitney test is applied to the repeated hospital reports.',
 'All outcomes and count denominators are saved exactly in the population tables. Whole hospitals are resampled together. Profile membership is annual and can change within a service.',
 'PCA hulls describe the footprint of all assigned test points. They are not confidence regions.',
 'Primary signal-model mean predictions are not plotted; bars show observed signal fractions. The boxplot displays log(1+reported SSI rate per 1,000 operations), with zeros retained.',
 'K=3 is exploratory. The analysis demonstrates later-report associations conditional on the frozen profile definition; it does not show incremental clinical utility beyond the existing full prediction model.']
(O/'Methods_and_panel_guide.txt').write_text('\n\n'.join(notes)+'\n')
print(summary.to_string(index=False));print(reference.query("comparison=='Profile 3 versus Profile 2'").to_string(index=False));print('Selected procedures:',selected)
