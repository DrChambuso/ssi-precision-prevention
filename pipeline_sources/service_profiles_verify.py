from pathlib import Path
import json, hashlib, math
import numpy as np
import pandas as pd

ROOT=Path('__LEGACY_ROOT__')
O=ROOT/'work/ssi_figure17_redesign/fourpanel_prediction_analysis'
source=ROOT/'work/ssi_new_prediction/lagged_prediction_cohort.csv.gz'
raw=pd.read_csv(source)
train=pd.read_csv(O/'training_profile_assignments.csv')
test=pd.read_csv(O/'later_test_profile_assignments.csv')
scaling=pd.read_csv(O/'training_scaling.csv').set_index('feature')
centroids=pd.read_csv(O/'frozen_training_centroids.csv').set_index('profile')
rotation=pd.read_csv(O/'PCA_training_loadings.csv').set_index('feature')
features=['log_volume','log_expected_rate','log_prior_sir','log_history_sir']
audit={}
assert len(train)==39353 and len(test)==18132
assert not train.duplicated(['unit','year']).any() and not test.duplicated(['unit','year']).any()
assert train.year.max()<test.year.min()
max_projection_error=0
for dataset,frame in [('Training',train),('Test',test)]:
    original=raw[raw['set']==dataset].set_index(['unit','year']).reindex(pd.MultiIndex.from_frame(frame[['unit','year']]))
    for col in features:
        assert np.allclose(frame[col],original[col],rtol=0,atol=2e-13)
    if dataset=='Test':
        for col in ['n','y','e','outcome']:
            assert np.allclose(frame[col],original[col],rtol=0,atol=1e-10)
    X=(frame[features].to_numpy()-scaling.loc[features,'center'].to_numpy())/scaling.loc[features,'SD'].to_numpy()
    distance=np.stack([((X-centroids.loc[k,features].to_numpy())**2).sum(axis=1) for k in [1,2,3]],axis=1)
    predicted=distance.argmin(axis=1)+1
    assert np.array_equal(predicted,frame.profile)
    pc=X@rotation.loc[features,['PC1','PC2','PC3','PC4']].to_numpy()
    max_projection_error=max(max_projection_error,float(np.abs(pc-frame[['PC1','PC2','PC3','PC4']].to_numpy()).max()))
    assert max_projection_error<1e-10
    if dataset=='Training':
        assert np.allclose(X.mean(axis=0),0,atol=1e-12)
        assert np.allclose(X.std(axis=0,ddof=1),1,atol=1e-12)
        for k in [1,2,3]:assert np.allclose(X[frame.profile==k].mean(axis=0),centroids.loc[k,features],rtol=0,atol=1e-12)
assert np.allclose(rotation.to_numpy().T@rotation.to_numpy(),np.eye(4),atol=1e-12)
audit['all_training_and_test_assignments_independently_reconstructed']=True
audit['frozen_PCA_projection_max_error']=max_projection_error
audit['training_centroids_equal_within_profile_feature_means']=True
audit['future_outcomes_excluded_from_clustering_feature_list']=True

summary=pd.read_csv(O/'panel_b_prevalence_and_all_profile_outcomes.csv')
assert summary.reports.sum()==18132 and summary.operations.sum()==1959747 and summary.SSI_cases.sum()==11897 and summary.signals.sum()==3540
sites,si=np.unique(test.site,return_inverse=True)
assert len(sites)==337
rng=np.random.default_rng(20261021)
weights=rng.multinomial(len(sites),np.repeat(1/len(sites),len(sites)),size=1999)
CI_errors=[]
for k in [1,2,3]:
    mask=(test.profile.to_numpy()==k);r=summary.set_index('profile').loc[k]
    counts=np.stack([np.bincount(si,weights=mask,minlength=len(sites)),
                     np.bincount(si,weights=mask*test.outcome.to_numpy(),minlength=len(sites)),
                     np.bincount(si,weights=mask*test.n.to_numpy(),minlength=len(sites)),
                     np.bincount(si,weights=mask*test.y.to_numpy(),minlength=len(sites)),
                     np.bincount(si,weights=mask*(test.y.to_numpy()>0),minlength=len(sites))],axis=1)
    draws=weights@counts
    assert counts[:,0].sum()==r.reports and counts[:,1].sum()==r.signals and counts[:,2].sum()==r.operations and counts[:,3].sum()==r.SSI_cases
    for metric,values in [('signal_fraction',draws[:,1]/draws[:,0]),('SSI_rate_per_1000',1000*draws[:,3]/draws[:,2]),('SSI_positive_report_fraction',draws[:,4]/draws[:,0])]:
        lo,hi=np.quantile(values,[.025,.975]);CI_errors.extend([abs(lo-r[metric+'_lower']),abs(hi-r[metric+'_upper'])])
        assert r[metric+'_lower']<=r[metric]<=r[metric+'_upper']
audit['hospital_bootstrap_CI_max_error']=max(CI_errors)
assert max(CI_errors)<1e-12
audit['bootstrap_seed_and_whole_hospital_frame_verified']=True
audit['test_population_reconciles_to_source']=True

coef=pd.read_csv(O/'profile_future_outcome_all_coefficients.csv')
errors=[]
for name,g in coef.groupby('model'):
    design=pd.read_csv(O/(name+'_verification_design.csv'))
    X=design.iloc[:,6:].to_numpy();mu=design.fitted_value.to_numpy()
    y=design.outcome.to_numpy() if 'signal' in name else design.y.to_numpy()
    Hinv=np.linalg.inv(X.T@(X*mu[:,None]));score=X*(y-mu)[:,None]
    sites,si=np.unique(design.site,return_inverse=True);U=np.zeros((len(sites),X.shape[1]));np.add.at(U,si,score)
    N,P=X.shape;G=len(sites);V=Hinv@(U.T@U)@Hinv*G/(G-1)*(N-1)/(N-P)
    mapped=g.set_index('term')
    for j,term in enumerate(design.columns[6:]):errors.append(abs(np.sqrt(V[j,j])-mapped.loc[term,'robust_SE']))
    assert np.isfinite(V).all()
audit['four_model_independent_robust_SE_max_error']=max(errors)
assert max(errors)<1e-8
primary=pd.read_csv(O/'profile_future_outcome_pairwise_contrasts.csv')
ref=pd.read_csv(O/'profile_future_contrasts_reference_profile2.csv')
for row in ref.itertuples():
    g=primary[primary.model==row.model].set_index('comparison')
    if row.comparison=='Profile 1 versus Profile 2':
        z=g.loc['Profile 2 versus Profile 1'];assert np.isclose(row.effect,1/z.effect);assert np.isclose(row.lower,1/z.upper);assert np.isclose(row.upper,1/z.lower)
    else:z=g.loc[row.comparison];assert np.isclose(row.effect,z.effect)
    assert math.isclose(row.p,z.p,rel_tol=1e-12,abs_tol=0) and math.isclose(row.q_BH,z.q_BH,rel_tol=1e-12,abs_tol=0)
audit['reference_profile2_contrasts_exact_reexpressions']=True

heat=pd.read_csv(O/'panel_c_training_components_and_procedure_mix.csv')
for _,g in heat.groupby('row'):
    assert np.isclose(g.row_standardized_value.mean(),0,atol=1e-12)
    assert np.isclose(g.row_standardized_value.std(ddof=1),1,atol=1e-12)
    for row in g.itertuples():
        if row.block=='Training procedure mix':
            subset=train[train.profile==row.profile];n=(subset.procedure==row.row).sum()
            assert n==row.reports;assert np.isclose(row.raw_value,n/len(subset))
        else:assert np.isfinite(row.raw_value)
audit['heatmap_training_components_and_procedure_denominators_verified']=True
box=pd.read_csv(O/'panel_d_all_11502_report_rates.csv')
assert len(box)==11502 and set(box.profile)=={2,3}
assert (box.y==0).sum()==6966
assert np.allclose(box.SSI_rate_per_1000,1000*box.y/box.n)
assert np.allclose(box.log1p_SSI_rate_per_1000,np.log1p(box.SSI_rate_per_1000))
assert box.n.sum()==1887586 and box.y.sum()==11424
audit['panel_d_all_report_values_and_zero_counts_verified']=True
audit['panel_d_display_reports']=len(box)
audit['panel_d_model_reports']=18132
audit['panel_d_zero_SSI_reports']=int((box.y==0).sum())
audit['training_clustering_diagnostics']=pd.read_csv(O/'training_clustering_diagnostics.csv').to_dict('records')
audit['model_warning_rows']=len(pd.read_csv(O/'model_warnings.csv'))
assert audit['model_warning_rows']==0
meta=json.loads((O/'fourpanel_analysis.json').read_text())
assert hashlib.sha256(source.read_bytes()).hexdigest()==meta['source_sha256']
audit['source_hash_unchanged']=True
prohibited='\u2010\u2011\u2012\u2013\u2014\u2015\u2212'
bad=[]
for p in O.iterdir():
    if p.suffix in ['.csv','.json','.txt','.R','.py','.log']:
        txt=p.read_text()
        if any(ch in txt for ch in prohibited):bad.append(p.name)
assert not bad,bad
audit['prohibited_dash_files']=bad;audit['status']='PASS'
(O/'independent_verification.json').write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps(audit,indent=2))
