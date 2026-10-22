options(stringsAsFactors=FALSE,scipen=8)
ROOT<-'__LEGACY_ROOT__'
OUT<-file.path(ROOT,'work/ssi_inferential_stats')
d<-read.csv(gzfile(file.path(ROOT,'outputs/SSI_Prevention_Intelligence/SSI_Signal_Memory_Vector_Atlas/reproducibility/annual_reports.csv.gz')))
base<-aggregate(d[d$year<=2019,c('n','y','e')],list(unit=d$unit[d$year<=2019]),sum)
names(base)[2:4]<-c('baseline_n','baseline_y','baseline_e')
base$baseline_report_years<-as.numeric(table(d$unit[d$year<=2019])[base$unit])
g<-d[d$year>=2022 & !is.na(d$alert_lag1) & !is.na(d$alert_lag2),]
g<-merge(g,base,by='unit',all.x=TRUE,sort=FALSE)
audit<-data.frame(population=c('All target 2022-2025 reports with two consecutive prior years','Eligible reports with at least one 2016-2019 baseline report'),
 reports=c(nrow(g),sum(!is.na(g$baseline_n))),units=c(length(unique(g$unit)),length(unique(g$unit[!is.na(g$baseline_n)]))),
 sites=c(length(unique(g$site)),length(unique(g$site[!is.na(g$baseline_n)]))),alerts=c(sum(g$alert),sum(g$alert[!is.na(g$baseline_n)])),
 operations=c(sum(g$n),sum(g$n[!is.na(g$baseline_n)])),SSI_cases=c(sum(g$y),sum(g$y[!is.na(g$baseline_n)])))
write.csv(audit,file.path(OUT,'earlier_service_context_sample_size.csv'),row.names=FALSE)
g<-g[!is.na(g$baseline_n),]
g$history<-factor(paste0(as.integer(g$alert_lag2),as.integer(g$alert_lag1)),levels=c('00','01','10','11'))
g$log_prior_volume<-log1p(g$n_lag1)
g$log_prior_expected_rate<-log((g$e_lag1+.5)/(g$n_lag1+1))
g$log_baseline_OE<-log((g$baseline_y+.5)/(g$baseline_e+.5))
g$log_baseline_volume<-log1p(g$baseline_n)
g$age<-factor(g$age);g$procedure<-factor(g$procedure);g$year_f<-factor(g$year)
warnings_log<-data.frame(model=character(),warning=character())
form<-alert~history+log_prior_volume+log_prior_expected_rate+log_baseline_OE+log_baseline_volume+age+procedure+year_f
fits<-list();coefrows<-list();diagnostics<-list()
for(family_name in c('Poisson','Logistic')) {
  fam<-if(family_name=='Poisson')poisson(link='log')else binomial()
  fit<-withCallingHandlers(glm(form,data=g,family=fam,control=glm.control(maxit=100)),warning=function(w){warnings_log<<-rbind(warnings_log,data.frame(model=family_name,warning=conditionMessage(w)));invokeRestart('muffleWarning')})
  stopifnot(fit$converged,all(is.finite(coef(fit))))
  X<-model.matrix(fit);y<-g$alert;mu<-fitted(fit);W<-if(family_name=='Poisson')mu else mu*(1-mu)
  Hinv<-solve(crossprod(X,X*W));U<-rowsum(X*as.numeric(y-mu),g$site,reorder=FALSE)
  N<-nrow(X);K<-nrow(U);P<-ncol(X);V<-Hinv%*%crossprod(U)%*%Hinv*K/(K-1)*(N-1)/(N-P)
  b<-coef(fit);se<-sqrt(diag(V));z<-b/se
  cf<-data.frame(model=family_name,term=names(b),log_effect=b,robust_SE=se,effect=exp(b),lower=exp(b-1.96*se),upper=exp(b+1.96*se),p=2*pnorm(abs(z),lower.tail=FALSE),
    reports=N,units=length(unique(g$unit)),sites=K,operations=sum(g$n),SSI_cases=sum(g$y),alerts=sum(y))
  coefrows[[length(coefrows)+1]]<-cf;fits[[family_name]]<-list(fit=fit,V=V)
  diagnostics[[length(diagnostics)+1]]<-data.frame(model=family_name,converged=fit$converged,iterations=fit$iter,fitted_min=min(mu),fitted_max=max(mu),maximum_abs_coefficient=max(abs(b)))
  ix<-grep('history',names(b));bb<-b[ix];vv<-V[ix,ix];chi<-as.numeric(t(bb)%*%solve(vv)%*%bb)
  write.csv(data.frame(df=3,Wald_chisq=chi,p=pchisq(chi,3,lower.tail=FALSE)),file.path(OUT,paste0('earlier_service_context_',tolower(family_name),'_global_test.csv')),row.names=FALSE)
  if(family_name=='Poisson')write.csv(cbind(g[c('site','unit','alert')],fitted_value=mu,as.data.frame(X)),file.path(OUT,'earlier_service_context_Poisson_verification_design.csv'),row.names=FALSE)
}
write.csv(do.call(rbind,coefrows),file.path(OUT,'earlier_service_context_all_coefficients.csv'),row.names=FALSE)
write.csv(do.call(rbind,diagnostics),file.path(OUT,'earlier_service_context_model_diagnostics.csv'),row.names=FALSE)
write.csv(warnings_log,file.path(OUT,'earlier_service_context_warnings.csv'),row.names=FALSE)
logit<-fits[['Logistic']];b<-coef(logit$fit);V<-logit$V
marg<-list()
for(h in levels(g$history)) {
  nd<-g;nd$history<-factor(h,levels=levels(g$history));X<-model.matrix(delete.response(terms(logit$fit)),nd)
  pr<-plogis(X%*%b);grad<-colMeans(X*as.numeric(pr*(1-pr)))
  marg[[h]]<-list(prob=mean(pr),grad=grad)
}
probrows<-lapply(names(marg),function(h){a<-marg[[h]];se<-sqrt(as.numeric(t(a$grad)%*%V%*%a$grad));data.frame(history=h,standardized_alert_probability=a$prob,lower=max(0,a$prob-1.96*se),upper=min(1,a$prob+1.96*se),robust_SE=se)})
write.csv(do.call(rbind,probrows),file.path(OUT,'earlier_service_context_standardized_probabilities.csv'),row.names=FALSE)
rows<-list()
for(cmp in list(c('10','00'),c('01','00'),c('11','00'),c('10','01'),c('11','10'),c('11','01'))) {
  a<-marg[[cmp[1]]];z<-marg[[cmp[2]]];val<-log(a$prob/z$prob);grad<-a$grad/a$prob-z$grad/z$prob;se<-sqrt(as.numeric(t(grad)%*%V%*%grad))
  rd<-a$prob-z$prob;grd<-a$grad-z$grad;srd<-sqrt(as.numeric(t(grd)%*%V%*%grd))
  rows[[length(rows)+1]]<-data.frame(comparison=paste(cmp,collapse=' versus '),RR=exp(val),lower=exp(val-1.96*se),upper=exp(val+1.96*se),p=2*pnorm(abs(val/se),lower.tail=FALSE),risk_difference=rd,RD_lower=rd-1.96*srd,RD_upper=rd+1.96*srd,RD_p=2*pnorm(abs(rd/srd),lower.tail=FALSE))
}
z<-do.call(rbind,rows);z$q_BH<-p.adjust(z$p,'BH');write.csv(z,file.path(OUT,'earlier_service_context_standardized_contrasts.csv'),row.names=FALSE)
write.csv(g[c('unit','site','age','procedure','year','history','alert','n','y','e','baseline_n','baseline_y','baseline_e','baseline_report_years')],file.path(OUT,'earlier_service_context_analysis_cohort.csv'),row.names=FALSE)
writeLines(c('Prospectively separated earlier-service-context sensitivity.',
 'Earlier context: all available annual reports in 2016-2019, pooled within hospital-age-procedure unit. Requires at least one observed baseline year.',
 'Target reports: 2022-2025, requiring both immediately preceding annual reports. Target-year two-year histories therefore use 2020 onward and do not overlap the 2016-2019 context.',
 'Model: target annual-report alert as a function of two-year signal history, log1p(prior operations), smoothed prior expected SSI rate, smoothed baseline observed/predicted SSI ratio, log1p(baseline operations), age, procedure, calendar year.',
 'All model variables precede the target report. The earlier service context is an observed historical covariate, not a unit fixed effect or complete measure of stable service characteristics.',
 'Modified-Poisson model provides adjusted report-alert risk ratios with hospital-cluster robust variance and CR1 correction. Its working means are not plotted as probabilities.',
 'Logistic sensitivity provides bounded standardized probabilities by averaging fitted predictions over the eligible covariate distribution after assigning each history category. Robust delta-method intervals and contrasts reflect coefficient uncertainty.',
 'The effects describe surveillance associations and predictive context. They do not estimate an intervention effect of changing a hospital history.',
 'Multiplicity: six pre-specified history contrasts adjusted by Benjamini-Hochberg.'),file.path(OUT,'earlier_service_context_methods.txt'))
print(audit);print(do.call(rbind,coefrows)[grepl('history',do.call(rbind,coefrows)$term),]);print(z)
