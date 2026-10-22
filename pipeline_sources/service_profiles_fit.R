options(stringsAsFactors=FALSE,scipen=8)
ROOT<-'__LEGACY_ROOT__'
OUT<-file.path(ROOT,'work/ssi_figure17_redesign/fourpanel_prediction_analysis')
dir.create(OUT,recursive=TRUE,showWarnings=FALSE)
input<-file.path(ROOT,'work/ssi_new_prediction/lagged_prediction_cohort.csv.gz')
d<-read.csv(gzfile(input));train<-d[d$set=='Training',];test<-d[d$set=='Test',]
stopifnot(nrow(train)==39353,nrow(test)==18132,all(train$year<min(test$year)),!anyDuplicated(paste(d$unit,d$year)))
features<-c('log_volume','log_expected_rate','log_prior_sir','log_history_sir')
center<-vapply(train[features],mean,numeric(1));scalev<-vapply(train[features],sd,numeric(1))
X<-scale(as.matrix(train[features]),center=center,scale=scalev)
Z<-scale(as.matrix(test[features]),center=center,scale=scalev)
stopifnot(all(is.finite(X)),all(is.finite(Z)))
set.seed(20261019)
km<-kmeans(X,centers=3,nstart=100,iter.max=100,algorithm='Hartigan-Wong')
stopifnot(km$ifault==0)
# Labels are fixed using increasing training-center log-volume, without outcomes.
order_old<-order(km$centers[,'log_volume'])
newid<-integer(3);newid[order_old]<-1:3
centroids<-km$centers[order_old,,drop=FALSE];rownames(centroids)<-paste0('Profile ',1:3)
write.csv(data.frame(training_reports=nrow(train),training_sites=length(unique(train$site)),k=3,nstart=100,seed=20261019,
 iterations=km$iter,ifault=km$ifault,total_sum_of_squares=km$totss,within_sum_of_squares=km$tot.withinss,between_sum_of_squares=km$betweenss),
 file.path(OUT,'training_clustering_diagnostics.csv'),row.names=FALSE)
train$profile<-newid[km$cluster]
distances<-sapply(1:3,function(k)rowSums((sweep(Z,2,centroids[k,],'-'))^2))
test$profile<-max.col(-distances,ties.method='first')
pca<-prcomp(X,center=FALSE,scale.=FALSE)
train_projection<-X%*%pca$rotation;test_projection<-Z%*%pca$rotation
for(j in 1:4){train[[paste0('PC',j)]]<-train_projection[,j];test[[paste0('PC',j)]]<-test_projection[,j]}
for(j in seq_along(features)){train[[paste0(features[j],'_z')]]<-X[,j];test[[paste0(features[j],'_z')]]<-Z[,j]}
train$SSI_rate_per_1000<-1000*train$y/train$n;test$SSI_rate_per_1000<-1000*test$y/test$n
test$log1p_SSI_rate_per_1000<-log1p(test$SSI_rate_per_1000)
test$any_SSI<-as.integer(test$y>0)
cols<-c('unit','site','age','procedure','year','profile','n','y','e','outcome','any_SSI','SSI_rate_per_1000','log1p_SSI_rate_per_1000',paste0('PC',1:4),features,paste0(features,'_z'))
write.csv(test[cols],file.path(OUT,'later_test_profile_assignments.csv'),row.names=FALSE)
write.csv(train[c('unit','site','age','procedure','year','profile',paste0('PC',1:4),features,paste0(features,'_z'))],file.path(OUT,'training_profile_assignments.csv'),row.names=FALSE)
write.csv(data.frame(feature=features,center=center,SD=scalev),file.path(OUT,'training_scaling.csv'),row.names=FALSE)
write.csv(data.frame(profile=1:3,centroids),file.path(OUT,'frozen_training_centroids.csv'),row.names=FALSE)
write.csv(data.frame(feature=rownames(pca$rotation),pca$rotation),file.path(OUT,'PCA_training_loadings.csv'),row.names=FALSE)
variance<-pca$sdev^2/sum(pca$sdev^2)
write.csv(data.frame(component=paste0('PC',1:4),variance_fraction=variance,cumulative_fraction=cumsum(variance)),file.path(OUT,'PCA_training_explained_variance.csv'),row.names=FALSE)
saveRDS(list(kmeans=km,order_old=order_old,centroids=centroids,center=center,scale=scalev,PCA=pca,seed=20261019),file.path(OUT,'frozen_profile_definition.rds'))
summaries<-list()
for(set in c('Training','Test')) {
 g<-if(set=='Training')train else test
 for(k in 1:3) {
  q<-g[g$profile==k,]
  summaries[[length(summaries)+1]]<-data.frame(dataset=set,profile=k,reports=nrow(q),sites=length(unique(q$site)),units=length(unique(q$unit)),
   operations=sum(q$n),SSI_cases=sum(q$y),signals=sum(q$outcome),signal_fraction=mean(q$outcome),SSI_rate_per_1000=1000*sum(q$y)/sum(q$n),
   SSI_positive_reports=sum(q$y>0),SSI_positive_fraction=mean(q$y>0),median_report_SSI_rate=median(q$SSI_rate_per_1000),
   Q1_report_SSI_rate=quantile(q$SSI_rate_per_1000,.25),Q3_report_SSI_rate=quantile(q$SSI_rate_per_1000,.75),
   median_prior_volume=median(q$n_lag1),median_prior_cases=median(q$y_lag1),median_prior_expected=median(q$e_lag1),
   median_prior_OE_smoothed=median(q$prior_sir),median_history_OE_smoothed=median(q$history_sir))
 }
}
write.csv(do.call(rbind,summaries),file.path(OUT,'profile_population_and_outcomes.csv'),row.names=FALSE)
components<-list()
for(set in c('Training','Test'))for(k in 1:3)for(f in features) {
 q<-if(set=='Training')train[train$profile==k,] else test[test$profile==k,]
 components[[length(components)+1]]<-data.frame(dataset=set,profile=k,feature=f,mean_training_z=mean(q[[paste0(f,'_z')]]),
 median_training_z=median(q[[paste0(f,'_z')]]),median_unstandardized=median(q[[f]]))
}
write.csv(do.call(rbind,components),file.path(OUT,'component_heatmap_values.csv'),row.names=FALSE)
composition<-as.data.frame(table(test$profile,test$procedure));names(composition)<-c('profile','procedure','reports')
composition$profile<-as.integer(composition$profile)
composition$profile_fraction<-composition$reports/ave(composition$reports,composition$profile,FUN=sum)
overall<-table(test$procedure)/nrow(test)
composition$overall_fraction<-as.numeric(overall[composition$procedure]);composition$relative_representation<-composition$profile_fraction/composition$overall_fraction
write.csv(composition,file.path(OUT,'later_procedure_composition_descriptive.csv'),row.names=FALSE)
agecomp<-as.data.frame(table(test$profile,test$age));names(agecomp)<-c('profile','age','reports');agecomp$within_profile_fraction<-agecomp$reports/ave(agecomp$reports,agecomp$profile,FUN=sum)
write.csv(agecomp,file.path(OUT,'later_age_composition_descriptive.csv'),row.names=FALSE)

# All projections supplied; optional display sampling is random within the already frozen profile.
set.seed(20261020)
show<-unlist(lapply(1:3,function(k){i<-which(test$profile==k);sample(i,min(length(i),1000))}))
write.csv(test[show,cols],file.path(OUT,'optional_PCA_display_sample_3000.csv'),row.names=FALSE)
hulls<-list()
for(k in 1:3){g<-test[test$profile==k,];ix<-chull(g$PC1,g$PC2);hulls[[k]]<-data.frame(profile=k,vertex=seq_along(ix),PC1=g$PC1[ix],PC2=g$PC2[ix])}
write.csv(do.call(rbind,hulls),file.path(OUT,'all_test_points_convex_hulls.csv'),row.names=FALSE)

warnings_log<-data.frame(model=character(),warning=character());allcf<-list();globals<-list();contrasts<-list()
test$profile_f<-factor(test$profile,levels=1:3);test$age<-factor(test$age);test$procedure<-factor(test$procedure);test$year_f<-factor(test$year)
robust<-function(form,name) {
 f<-withCallingHandlers(glm(form,data=test,family=poisson(link='log'),control=glm.control(maxit=100)),warning=function(w){warnings_log<<-rbind(warnings_log,data.frame(model=name,warning=conditionMessage(w)));invokeRestart('muffleWarning')})
 stopifnot(f$converged,all(is.finite(coef(f))))
 x<-model.matrix(f);mu<-fitted(f);response<-model.response(model.frame(f))
 Hinv<-solve(crossprod(x,x*mu));U<-rowsum(x*as.numeric(response-mu),test$site,reorder=FALSE);N<-nrow(x);G<-nrow(U);P<-ncol(x)
 V<-Hinv%*%crossprod(U)%*%Hinv*G/(G-1)*(N-1)/(N-P)
 b<-coef(f);se<-sqrt(diag(V));stopifnot(all(is.finite(se)),all(se>0))
 cf<-data.frame(model=name,term=names(b),log_effect=b,robust_SE=se,effect=exp(b),lower=exp(b-1.96*se),upper=exp(b+1.96*se),p=2*pnorm(abs(b/se),lower.tail=FALSE),reports=N,sites=G,
  fitted_min=min(mu),fitted_max=max(mu),converged=f$converged,iterations=f$iter)
 allcf[[length(allcf)+1]]<<-cf
 ids<-which(names(b)%in%c('profile_f2','profile_f3'));bb<-b[ids];vv<-V[ids,ids];wald<-as.numeric(t(bb)%*%solve(vv)%*%bb)
 globals[[length(globals)+1]]<<-data.frame(model=name,df=2,Wald_chisq=wald,p=pchisq(wald,2,lower.tail=FALSE))
 for(cmp in list(c(2,1),c(3,1),c(3,2))) {
  L<-rep(0,length(b));names(L)<-names(b)
  if(cmp[1]!=1)L[paste0('profile_f',cmp[1])]<-1
  if(cmp[2]!=1)L[paste0('profile_f',cmp[2])]<--1
  v<-sum(L*b);s<-sqrt(as.numeric(t(L)%*%V%*%L))
  contrasts[[length(contrasts)+1]]<<-data.frame(model=name,comparison=paste0('Profile ',cmp[1],' versus Profile ',cmp[2]),effect=exp(v),lower=exp(v-1.96*s),upper=exp(v+1.96*s),robust_SE=s,p=2*pnorm(abs(v/s),lower.tail=FALSE),reports=N,sites=G)
 }
 write.csv(cbind(test[c('site','unit','outcome','y','n')],fitted_value=mu,as.data.frame(x)),file.path(OUT,paste0(name,'_verification_design.csv')),row.names=FALSE)
}
robust(outcome~profile_f+age+procedure+year_f,'future_signal_adjusted_RR')
robust(y~profile_f+age+procedure+year_f+offset(log(n)),'future_SSI_incidence_adjusted_IRR')
# Sensitivity adjustment for two non-burden features used to construct the profiles.
robust(outcome~profile_f+age+procedure+year_f+log_volume+log_expected_rate,'future_signal_volume_expected_rate_sensitivity_RR')
robust(y~profile_f+age+procedure+year_f+log_volume+log_expected_rate+offset(log(n)),'future_incidence_volume_expected_rate_sensitivity_IRR')
con<-do.call(rbind,contrasts);con$q_BH<-ave(con$p,con$model,FUN=function(x)p.adjust(x,'BH'))
write.csv(con,file.path(OUT,'profile_future_outcome_pairwise_contrasts.csv'),row.names=FALSE)
write.csv(do.call(rbind,globals),file.path(OUT,'profile_future_outcome_global_tests.csv'),row.names=FALSE)
write.csv(do.call(rbind,allcf),file.path(OUT,'profile_future_outcome_all_coefficients.csv'),row.names=FALSE)
write.csv(warnings_log,file.path(OUT,'model_warnings.csv'),row.names=FALSE)
writeLines(capture.output(sessionInfo()),file.path(OUT,'R_session_information.txt'))
print(do.call(rbind,summaries));print(con);print(do.call(rbind,globals));print(centroids);print(variance)
