options(stringsAsFactors=FALSE,scipen=8)
suppressPackageStartupMessages(library(survival))
ROOT<-'__LEGACY_ROOT__'
OUT<-file.path(ROOT,'work/ssi_inferential_stats')
g<-read.csv(gzfile(file.path(ROOT,'outputs/SSI_Prevention_Intelligence/SSI_Signal_Memory_Vector_Atlas/reproducibility/two_year_history_reports.csv.gz')))
g$history<-factor(sprintf('%02d',as.integer(g$history)),levels=c('00','01','10','11'))
g$log_prior_volume<-log1p(g$n_lag1)
g$log_prior_expected_rate<-log((g$e_lag1+.5)/(g$n_lag1+1))
g$year_f<-factor(g$year)
totals<-aggregate(g$alert,list(unit=g$unit),function(z)c(reports=length(z),alerts=sum(z),varies=length(unique(z))==2))
audit<-data.frame(unit=totals$unit,reports=totals$x[,'reports'],alerts=totals$x[,'alerts'],varies=totals$x[,'varies'])
g$included<-g$unit%in%audit$unit[audit$varies==1]
write.csv(audit,file.path(OUT,'within_unit_memory_eligibility.csv'),row.names=FALSE)
summaryrows<-data.frame(population=c('All three-year-history reports','Outcome-varying units contribute'),
 reports=c(nrow(g),sum(g$included)),units=c(length(unique(g$unit)),length(unique(g$unit[g$included]))),
 sites=c(length(unique(g$site)),length(unique(g$site[g$included]))),alerts=c(sum(g$alert),sum(g$alert[g$included])),
 operations=c(sum(g$n),sum(g$n[g$included])),SSI_cases=c(sum(g$y),sum(g$y[g$included])))
write.csv(summaryrows,file.path(OUT,'within_unit_memory_sample_size.csv'),row.names=FALSE)
g<-g[g$included,]
warns<-character()
fit<-withCallingHandlers(clogit(alert~history+log_prior_volume+log_prior_expected_rate+year_f+strata(unit),
 data=g,cluster=site,method='efron',x=TRUE,control=coxph.control(iter.max=100)),warning=function(w){warns<<-c(warns,conditionMessage(w));invokeRestart('muffleWarning')})
s<-summary(fit);ix<-grep('history',rownames(s$coefficients));cf<-s$coefficients[ix,,drop=FALSE];ci<-s$conf.int[ix,,drop=FALSE]
z<-data.frame(comparison=c('01 versus 00','10 versus 00','11 versus 00'),conditional_OR=ci[,'exp(coef)'],lower=ci[,'lower .95'],upper=ci[,'upper .95'],robust_SE=cf[,'robust se'],p=cf[,'Pr(>|z|)'])
z$q_BH<-p.adjust(z$p,'BH');z$reports<-nrow(g);z$units<-length(unique(g$unit));z$sites<-length(unique(g$site));z$alerts<-sum(g$alert)
write.csv(z,file.path(OUT,'within_unit_memory_conditional_OR.csv'),row.names=FALSE)
b<-coef(fit)[ix];V<-vcov(fit)[ix,ix];chi<-as.numeric(t(b)%*%solve(V)%*%b)
write.csv(data.frame(df=3,Wald_chisq=chi,p=pchisq(chi,3,lower.tail=FALSE)),file.path(OUT,'within_unit_memory_global_test.csv'),row.names=FALSE)
cf<-s$coefficients;ci<-s$conf.int
write.csv(data.frame(term=rownames(cf),conditional_OR=ci[,'exp(coef)'],lower=ci[,'lower .95'],upper=ci[,'upper .95'],robust_SE=cf[,'robust se'],p=cf[,'Pr(>|z|)']),file.path(OUT,'within_unit_memory_all_coefficients.csv'),row.names=FALSE)
writeLines(c('Sensitivity model: stratified conditional logistic association, Efron approximation for ties.',
 'The hospital-age-procedure unit is the conditioning stratum. Stable unit-level differences are removed by conditioning.',
 'Only units with both above-predicted and at/below-predicted target reports contribute information. This is a selected within-unit population.',
 'Covariates: two-year signal history, log1p(prior operations), half-count-smoothed prior expected SSI rate, calendar year factor.',
 'Uncertainty: robust sandwich clustered by canonical named hospital, retaining all its units together.',
 'Effects are conditional odds ratios, not risk ratios, and not patient-level infection odds.',
 'Efron estimates approximate the exact conditional likelihood when a unit has multiple above-predicted target reports.',
 'This is a dynamic panel: histories include lagged target outcomes. Ordinary conditional logistic strict exogeneity is not satisfied, and conditioning on short-unit outcome totals can induce dynamic-panel bias. Negative associations must not be interpreted as protective effects, nor as definitive adjustment for stable service risk.',
 'This exploratory diagnostic is subordinate to the prospectively separated earlier-service-context sensitivity, which uses nonoverlapping earlier reports and no future conditioning.',
 paste('Warnings:',if(length(warns))paste(warns,collapse='; ')else 'None')),file.path(OUT,'within_unit_memory_methods.txt'))
exact_fit<-clogit(alert~history+log_prior_volume+log_prior_expected_rate+year_f+strata(unit),data=g,method='exact',x=TRUE)
write.csv(data.frame(term=names(coef(exact_fit)),coefficient=coef(exact_fit),model_SE=sqrt(diag(vcov(exact_fit)))),file.path(OUT,'within_unit_exact_coefficients.csv'),row.names=FALSE)
saveRDS(exact_fit,file.path(OUT,'within_unit_exact_model.rds'))
saveRDS(model.matrix(exact_fit),file.path(OUT,'within_unit_exact_design.rds'))
write.csv(cbind(g[c('unit','site','alert')],as.data.frame(model.matrix(exact_fit))),file.path(OUT,'within_unit_exact_design.csv'),row.names=FALSE)
print(summaryrows);print(z);print(summary(fit))
