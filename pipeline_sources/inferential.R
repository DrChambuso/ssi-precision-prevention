options(stringsAsFactors=FALSE, scipen=8)
suppressPackageStartupMessages(library(survival))
ROOT <- '__LEGACY_ROOT__'
OUT <- file.path(ROOT,'work/ssi_inferential_stats')
SRC <- file.path(ROOT,'outputs/SSI_Prevention_Intelligence/SSI_Signal_Memory_Vector_Atlas/reproducibility')
dir.create(OUT, recursive=TRUE, showWarnings=FALSE)
d <- read.csv(gzfile(file.path(SRC,'annual_reports.csv.gz')))
stopifnot(nrow(d)==72854,sum(d$n)==6737972,sum(d$y)==37525,!anyDuplicated(paste(d$unit,d$year)))
warnings_log <- data.frame(model=character(),warning=character())
fits_log <- list(); all_coeff <- list(); globals <- list(); problems <- list()
capture_fit <- function(expr, name) {
  withCallingHandlers(tryCatch(expr,error=function(e) {
    problems[[length(problems)+1]] <<- data.frame(model=name,issue=conditionMessage(e)); NULL
  }), warning=function(w) {
    warnings_log <<- rbind(warnings_log,data.frame(model=name,warning=conditionMessage(w)))
    invokeRestart('muffleWarning')
  })
}
setup_factors <- function(g) {
  g$age <- relevel(factor(g$age),'Adult')
  g$procedure <- factor(g$procedure)
  if ('Colon surgery' %in% levels(g$procedure)) g$procedure <- relevel(g$procedure,'Colon surgery')
  g$year_f <- factor(g$year)
  g$year_center <- g$year-2016
  if ('n_lag1' %in% names(g)) {
    g$log_prior_volume <- log1p(g$n_lag1)
    g$log_prior_expected_rate <- log((g$e_lag1+.5)/(g$n_lag1+1))
  }
  g
}
d <- setup_factors(d)
robust_glm <- function(formula, g, name, family=poisson(link='log')) {
  fit <- capture_fit(glm(formula,data=g,family=family,control=glm.control(maxit=100)),name)
  if (is.null(fit)) return(NULL)
  if (!fit$converged) {
    problems[[length(problems)+1]] <<- data.frame(model=name,issue='GLM did not converge; coefficients not reported.');return(NULL)
  }
  X <- model.matrix(fit); good <- !is.na(coef(fit)); X<-X[,good,drop=FALSE]
  mu <- fitted(fit); score <- X*as.numeric(g$alert-mu)
  if (identical(family$family,'poisson')) {
    response <- model.response(model.frame(fit)); score <- X*as.numeric(response-mu)
    W <- mu
  } else if (identical(family$family,'binomial')) {
    response <- model.response(model.frame(fit)); score <- X*as.numeric(response-mu)
    W <- mu*(1-mu)
  } else if (identical(family$family,'gaussian')) {
    response <- model.response(model.frame(fit)); score <- X*as.numeric(response-mu)
    W <- rep(1,length(mu))
  } else stop('Unsupported family')
  H <- crossprod(X,X*W)
  Hinv <- tryCatch(solve(H),error=function(e) NULL)
  if(is.null(Hinv)) {
    problems[[length(problems)+1]] <<- data.frame(model=name,issue='Singular information matrix; coefficients not reported.');return(NULL)
  }
  U <- rowsum(score,g$site,reorder=FALSE)
  N <- nrow(X); K <- nrow(U); P <- ncol(X)
  correction <- K/(K-1)*(N-1)/(N-P)
  V <- Hinv%*%crossprod(U)%*%Hinv*correction
  if(any(!is.finite(V)) || any(diag(V)<=0)) {
    problems[[length(problems)+1]] <<- data.frame(model=name,issue='Nonfinite or nonpositive robust covariance diagonal; coefficients not reported.');return(NULL)
  }
  beta <- coef(fit)[good]; se<-sqrt(diag(V)); z<-beta/se; p<-2*pnorm(abs(z),lower.tail=FALSE)
  cf <- data.frame(model=name,term=names(beta),log_effect=as.numeric(beta),robust_SE=as.numeric(se),
    effect=exp(beta),lower=exp(beta-1.96*se),upper=exp(beta+1.96*se),z=as.numeric(z),p=as.numeric(p),
    reports=N,sites=K,operations=sum(g$n),SSI_cases=sum(g$y),alerts=sum(g$alert),converged=fit$converged)
  all_coeff[[length(all_coeff)+1]] <<- cf
  fits_log[[length(fits_log)+1]] <<- data.frame(model=name,reports=N,sites=K,coefficients=P,rank=fit$rank,
    converged=fit$converged,iterations=fit$iter,response_range=paste(range(response),collapse=' to '),
    fitted_range=paste(signif(range(mu),5),collapse=' to '),maximum_abs_coefficient=max(abs(beta)),
    min_information_eigenvalue=min(eigen(H,symmetric=TRUE,only.values=TRUE)$values))
  asn <- attr(model.matrix(fit),'assign')[good]
  labels <- attr(terms(fit),'term.labels')
  for (j in seq_along(labels)) {
    ind <- which(asn==j)
    if (!length(ind)) next
    vv<-V[ind,ind,drop=FALSE];bb<-beta[ind]
    ev<-eigen(vv,symmetric=TRUE); keep<-ev$values>max(ev$values)*1e-10
    df<-sum(keep)
    wald<-if(df)sum((crossprod(ev$vectors[,keep,drop=FALSE],bb))^2/ev$values[keep]) else NA_real_
    globals[[length(globals)+1]] <<- data.frame(model=name,term=labels[j],df=df,Wald_chisq=wald,
      p=if(df)pchisq(wald,df,lower.tail=FALSE)else NA_real_,sites=K,reports=N)
  }
  list(fit=fit,V=V,coefficients=cf)
}
fit_overall_rate <- robust_glm(y~age+procedure+year_f+offset(log(n)),d,'SSI_rate_age_procedure_year')
fit_year_trend <- robust_glm(y~age+procedure+year_center+offset(log(n)),d,'SSI_rate_linear_year_trend')
pairs <- setup_factors(d[!is.na(d$alert_lag1),])
stopifnot(nrow(pairs)==57485)
fit_pairs <- robust_glm(alert~alert_lag1+log_prior_volume+log_prior_expected_rate+age+procedure+year_f,
  pairs,'Next_report_alert_prior_alert_adjusted')
fit_pair_rate <- robust_glm(y~alert_lag1+log_prior_volume+log_prior_expected_rate+age+procedure+year_f+offset(log(n)),
  pairs,'Next_report_SSI_rate_prior_alert_adjusted')
familyrows<-list()
for(label in c('All ages and procedures',sort(unique(pairs$family)))) {
  g<-droplevels(if(label=='All ages and procedures')pairs else pairs[pairs$family==label,])
  covariates<-paste(c('alert_lag1','log_prior_volume','log_prior_expected_rate',
    if(nlevels(g$age)>1)'age',if(nlevels(g$procedure)>1)'procedure','year_f'),collapse='+')
  ft<-robust_glm(as.formula(paste('y~',covariates,'+offset(log(n))')),g,paste0('Family_SSI_rate_prior_alert:',label))
  if(!is.null(ft)){z<-ft$coefficients[ft$coefficients$term=='alert_lag1',];z$group<-label;z$outcome<-'SSI rate';familyrows[[length(familyrows)+1]]<-z}
  ft<-robust_glm(as.formula(paste('alert~',covariates)),g,paste0('Family_next_report_alert:',label))
  if(!is.null(ft)){z<-ft$coefficients[ft$coefficients$term=='alert_lag1',];z$group<-label;z$outcome<-'Annual report alert';familyrows[[length(familyrows)+1]]<-z}
  workload_covariates<-paste(c('alert_lag1','log_prior_volume',if(nlevels(g$age)>1)'age',
    if(nlevels(g$procedure)>1)'procedure','year_f'),collapse='+')
  ft<-robust_glm(as.formula(paste('log1p(n)~',workload_covariates)),g,paste0('Family_current_workload:',label),gaussian())
  if(!is.null(ft)){z<-ft$coefficients[ft$coefficients$term=='alert_lag1',];z$group<-label;z$outcome<-'Geometric mean of operations plus 1';familyrows[[length(familyrows)+1]]<-z}
}
fam<-do.call(rbind,familyrows);fam$q_BH<-NA_real_
for(outcome in unique(fam$outcome)) {
 ind<-which(fam$outcome==outcome & fam$group!='All ages and procedures');fam$q_BH[ind]<-p.adjust(fam$p[ind],'BH')
}
write.csv(fam,file.path(OUT,'family_prior_signal_associations.csv'),row.names=FALSE)
trip <- setup_factors(pairs[!is.na(pairs$alert_lag2),])
trip$history <- factor(paste0(as.integer(trip$alert_lag2),as.integer(trip$alert_lag1)),levels=c('00','01','10','11'))
stopifnot(nrow(trip)==46465)
fit_trip <- robust_glm(alert~history+log_prior_volume+log_prior_expected_rate+age+procedure+year_f,
  trip,'Next_report_alert_two_year_memory_adjusted')
write.csv(cbind(trip[c('site','unit','alert')],fitted_value=fitted(fit_trip$fit),as.data.frame(model.matrix(fit_trip$fit))),
  file.path(OUT,'memory_GLM_score_verification_design.csv'),row.names=FALSE)
# Logistic sensitivity gives bounded probabilities and marginal contrasts over the same covariate distribution.
fit_trip_logit <- robust_glm(alert~history+log_prior_volume+log_prior_expected_rate+age+procedure+year_f,
  trip,'Two_year_memory_logistic_sensitivity',binomial())
if(!is.null(fit_trip_logit)) {
  b<-coef(fit_trip_logit$fit);V<-fit_trip_logit$V
  marginals<-list()
  for(h in levels(trip$history)) {
    nd<-trip;nd$history<-factor(h,levels=levels(trip$history))
    X<-model.matrix(delete.response(terms(fit_trip_logit$fit)),nd)
    pr<-plogis(X%*%b);grad<-colMeans(X*as.numeric(pr*(1-pr)))
    marginals[[h]]<-list(prob=mean(pr),grad=grad)
  }
  marginal_rows<-lapply(names(marginals),function(h) {
    a<-marginals[[h]];se<-sqrt(as.numeric(t(a$grad)%*%V%*%a$grad))
    data.frame(history=h,standardized_alert_probability=a$prob,lower=max(0,a$prob-1.96*se),upper=min(1,a$prob+1.96*se),robust_SE=se)
  })
  write.csv(do.call(rbind,marginal_rows),file.path(OUT,'two_year_memory_logistic_standardized_probabilities.csv'),row.names=FALSE)
  rows<-list()
  for(cmp in list(c('10','00'),c('01','00'),c('11','00'),c('10','01'),c('11','10'),c('11','01'))) {
    a<-marginals[[cmp[1]]];z<-marginals[[cmp[2]]]
    val<-log(a$prob/z$prob);grad<-a$grad/a$prob-z$grad/z$prob;se<-sqrt(as.numeric(t(grad)%*%V%*%grad))
    rd<-a$prob-z$prob;grd<-a$grad-z$grad;srd<-sqrt(as.numeric(t(grd)%*%V%*%grd))
    rows[[length(rows)+1]]<-data.frame(comparison=paste(cmp,collapse=' versus '),RR=exp(val),lower=exp(val-1.96*se),upper=exp(val+1.96*se),p=2*pnorm(abs(val/se),lower.tail=FALSE),
      risk_difference=rd,RD_lower=rd-1.96*srd,RD_upper=rd+1.96*srd,RD_p=2*pnorm(abs(rd/srd),lower.tail=FALSE))
  }
  z<-do.call(rbind,rows);z$q_BH<-p.adjust(z$p,'BH');write.csv(z,file.path(OUT,'two_year_memory_logistic_standardized_contrasts.csv'),row.names=FALSE)
}
contrast_rows <- list()
if(!is.null(fit_trip)) {
  terms<-names(coef(fit_trip$fit)); b<-coef(fit_trip$fit)
  for(cmp in list(c('history10','history00'),c('history01','history00'),c('history11','history00'),
                  c('history10','history01'),c('history11','history10'),c('history11','history01'))) {
    L<-rep(0,length(b));names(L)<-terms
    if(cmp[1]!='history00')L[cmp[1]]<-1
    if(cmp[2]!='history00')L[cmp[2]]<--1
    val<-sum(L*b);se<-sqrt(as.numeric(t(L)%*%fit_trip$V%*%L));p<-2*pnorm(abs(val/se),lower.tail=FALSE)
    contrast_rows[[length(contrast_rows)+1]]<-data.frame(comparison=paste(cmp,collapse=' versus '),log_RR=val,robust_SE=se,RR=exp(val),lower=exp(val-1.96*se),upper=exp(val+1.96*se),p=p)
  }
}
if(length(contrast_rows)) {
  z<-do.call(rbind,contrast_rows);z$q_BH<-p.adjust(z$p,'BH');write.csv(z,file.path(OUT,'two_year_memory_contrasts.csv'),row.names=FALSE)
}
proc_rows <- list(); period_rows<-list(); age_rows<-list(); trend_rows<-list()
for (proc in levels(d$procedure)) {
  g<-droplevels(pairs[pairs$procedure==proc,])
  cell<-table(factor(g$alert_lag1,levels=c(0,1)),factor(g$alert,levels=c(0,1)))
  if(length(unique(g$site))>=30 && all(rowSums(cell)>=10) && all(colSums(cell)>=10) && all(cell>=5)) {
    age_term<-if(nlevels(g$age)>1)'age+' else ''
    f<-as.formula(paste('alert~alert_lag1+log_prior_volume+log_prior_expected_rate+',age_term,'year_f'))
    ft<-robust_glm(f,g,paste0('Procedure_next_alert:',proc))
    if(!is.null(ft)) {z<-ft$coefficients[ft$coefficients$term=='alert_lag1',];z$procedure<-proc;proc_rows[[length(proc_rows)+1]]<-z}
  } else problems[[length(problems)+1]]<-data.frame(model=paste0('Procedure_next_alert:',proc),issue=paste('At least 30 sites and 5 outcomes per comparison cell required. Sites:',length(unique(g$site)),'Cells:',paste(cell,collapse=',')))
  g<-droplevels(d[d$procedure==proc & (d$year<=2019|d$year>=2022),]);g$late<-as.integer(g$year>=2022)
  if(length(unique(g$site))>=30 && sum(g$y[g$late==0])>=5 && sum(g$y[g$late==1])>=5) {
    f<-as.formula(paste('y~late+',if(nlevels(g$age)>1)'age+' else '','offset(log(n))'))
    ft<-robust_glm(f,g,paste0('Early_late_rate:',proc))
    if(!is.null(ft)){z<-ft$coefficients[ft$coefficients$term=='late',];z$procedure<-proc;period_rows[[length(period_rows)+1]]<-z}
  } else problems[[length(problems)+1]]<-data.frame(model=paste0('Early_late_rate:',proc),issue='At least 30 sites and 5 SSI cases in each period required.')
  g<-droplevels(d[d$procedure==proc,])
  if(length(unique(g$site))>=30 && nlevels(g$age)>1 && all(tapply(g$y,g$age,sum)>=5)) {
    ft<-robust_glm(y~age+year_f+offset(log(n)),g,paste0('Pediatric_adult_rate:',proc))
    if(!is.null(ft)){z<-ft$coefficients[ft$coefficients$term=='agePediatric',];z$procedure<-proc;age_rows[[length(age_rows)+1]]<-z}
  } else problems[[length(problems)+1]]<-data.frame(model=paste0('Pediatric_adult_rate:',proc),issue='Both age groups with at least 5 SSI cases required.')
  if(length(unique(g$site))>=30 && sum(g$y)>=20) {
    f<-as.formula(paste('y~year_center+',if(nlevels(g$age)>1)'age+' else '','offset(log(n))'))
    ft<-robust_glm(f,g,paste0('Procedure_rate_year_trend:',proc))
    if(!is.null(ft)){z<-ft$coefficients[ft$coefficients$term=='year_center',];z$procedure<-proc;trend_rows[[length(trend_rows)+1]]<-z}
  } else problems[[length(problems)+1]]<-data.frame(model=paste0('Procedure_rate_year_trend:',proc),issue='At least 30 sites and 20 SSI cases required.')
}
write_proc<-function(rows,name) {
  if(!length(rows))return(invisible(NULL))
  z<-do.call(rbind,rows);z$q_BH<-p.adjust(z$p,'BH',n=28);write.csv(z,file.path(OUT,name),row.names=FALSE)
}
write_proc(proc_rows,'procedure_prior_alert_adjusted_RR.csv')
write_proc(period_rows,'procedure_early_late_adjusted_IRR.csv')
write_proc(age_rows,'procedure_pediatric_adult_adjusted_IRR.csv')
write_proc(trend_rows,'procedure_annual_trend_adjusted_IRR.csv')

# Model calibration is assessed on untouched test predictions, with site-robust covariance.
pred<-read.csv(file.path(ROOT,'work/ssi_new_prediction/heldout_predictions.csv'))
cal_rows<-list();cal_globals<-list()
for(dataset in unique(pred$set)) {
  base<-pred[pred$set==dataset,]
  groups<-c('All ages and procedures','Adult','Pediatric')
  for(label in groups) {
    g<-if(label=='All ages and procedures')base else base[base$age==label,]
    if(nrow(g)<10 || length(unique(g$outcome))<2)next
    g$alert<-g$outcome;g$lp<-qlogis(g$combined)
    ft<-robust_glm(alert~lp,g,paste('Calibration_joint',dataset,label,sep=':'),binomial())
    if(!is.null(ft)) {
      z<-ft$coefficients;z$null_value<-ifelse(z$term=='lp',1,0)
      z$calibration_value<-z$log_effect;z$calibration_lower<-z$log_effect-1.96*z$robust_SE;z$calibration_upper<-z$log_effect+1.96*z$robust_SE
      z$p<-2*pnorm(abs((z$log_effect-z$null_value)/z$robust_SE),lower.tail=FALSE)
      z$dataset<-dataset;z$group<-label;cal_rows[[length(cal_rows)+1]]<-z
      diff<-coef(ft$fit)-c(0,1);wald<-as.numeric(t(diff)%*%solve(ft$V)%*%diff)
      cal_globals[[length(cal_globals)+1]]<-data.frame(dataset=dataset,group=label,Wald_chisq=wald,df=2,p=pchisq(wald,2,lower.tail=FALSE))
    }
  }
}
write.csv(do.call(rbind,cal_rows),file.path(OUT,'prediction_calibration_site_robust.csv'),row.names=FALSE)
write.csv(do.call(rbind,cal_globals),file.path(OUT,'prediction_calibration_joint_test.csv'),row.names=FALSE)

cohort<-read.csv(file.path(SRC,'maximum_time_to_alert_cohort.csv'))
stopifnot(nrow(cohort)==10081,!anyDuplicated(cohort$unit),sum(cohort$event)==4191)
coxrows<-list();phrows<-list();tvrows<-list()
groups<-c('All ages and procedures','Adult','Pediatric',sort(unique(cohort$procedure)))
for(label in groups) {
  g<-if(label=='All ages and procedures')cohort else if(label%in%c('Adult','Pediatric'))cohort[cohort$age==label,] else cohort[cohort$procedure==label,]
  if(nrow(g)<30 || length(unique(g$site))<30 || sum(g$event)<15 || length(unique(g$high))<2 || any(tapply(g$event,g$high,sum)<5)) {
    problems[[length(problems)+1]]<-data.frame(model=paste0('Cox:',label),issue='At least 30 units, 15 events, both baseline groups and 5 events per group required.');next
  }
  g$stratum<-interaction(g$age,g$procedure,g$baseline_year,drop=TRUE)
  fit<-capture_fit(coxph(Surv(time,event)~high+log1p(baseline_operations)+log1p(baseline_expected)+strata(stratum),
     data=g,ties='efron',cluster=site,robust=TRUE,x=TRUE,control=coxph.control(iter.max=100)),paste0('Cox:',label))
  if(is.null(fit))next
  s<-summary(fit);z<-s$coefficients['high',];v<-s$conf.int['high',]
  coxrows[[length(coxrows)+1]]<-data.frame(group=label,units=nrow(g),sites=length(unique(g$site)),events=sum(g$event),
    high_units=sum(g$high),low_units=sum(g$high==0),HR=v['exp(coef)'],lower=v['lower .95'],upper=v['upper .95'],p=z['Pr(>|z|)'],
    robust_SE=z['robust se'],iterations=fit$iter)
  ph<-capture_fit(cox.zph(fit,transform='km'),paste0('PH:',label))
  if(!is.null(ph)) {
    tab<-as.data.frame(ph$table);tab$term<-rownames(tab);tab$group<-label;phrows[[length(phrows)+1]]<-tab
  }
  if(TRUE) {
    tv<-capture_fit(coxph(Surv(time,event)~high+tt(high)+log1p(baseline_operations)+log1p(baseline_expected)+strata(stratum),
      data=g,ties='efron',cluster=site,robust=TRUE,tt=function(x,t,...)x*log1p(t),control=coxph.control(iter.max=100)),paste0('Cox_time_varying:',label))
    if(!is.null(tv))for(t in c(1,3,5,9)) {
      b<-coef(tv);V<-vcov(tv);L<-rep(0,length(b));names(L)<-names(b);L['high']<-1;L['tt(high)']<-log1p(t)
      val<-sum(L*b);se<-sqrt(as.numeric(t(L)%*%V%*%L))
      tvrows[[length(tvrows)+1]]<-data.frame(group=label,followup_year=t,HR=exp(val),lower=exp(val-1.96*se),upper=exp(val+1.96*se),p=2*pnorm(abs(val/se),lower.tail=FALSE),interaction_p=summary(tv)$coefficients['tt(high)','Pr(>|z|)'])
    }
  }
}
coxout<-do.call(rbind,coxrows);coxout$q_BH<-NA_real_
ind<-which(!coxout$group%in%c('All ages and procedures','Adult','Pediatric'));coxout$q_BH[ind]<-p.adjust(coxout$p[ind],'BH',n=28)
write.csv(coxout,file.path(OUT,'time_to_alert_cluster_adjusted_HR.csv'),row.names=FALSE)
write.csv(do.call(rbind,phrows),file.path(OUT,'proportional_hazards_diagnostics.csv'),row.names=FALSE)
write.csv(do.call(rbind,tvrows),file.path(OUT,'time_varying_high_baseline_HR.csv'),row.names=FALSE)
write.csv(do.call(rbind,all_coeff),file.path(OUT,'all_site_robust_GLM_coefficients.csv'),row.names=FALSE)
write.csv(do.call(rbind,globals),file.path(OUT,'all_site_robust_global_Wald_tests.csv'),row.names=FALSE)
write.csv(do.call(rbind,fits_log),file.path(OUT,'GLM_fit_diagnostics.csv'),row.names=FALSE)
write.csv(warnings_log,file.path(OUT,'all_model_warnings.csv'),row.names=FALSE)
write.csv(if(length(problems))do.call(rbind,problems)else data.frame(model=character(),issue=character()),file.path(OUT,'unavailable_or_failed_models.csv'),row.names=FALSE)
writeLines(capture.output(sessionInfo()),file.path(OUT,'R_session_information.txt'))
cat('Models:',length(fits_log),' Warnings:',nrow(warnings_log),' Skipped/failed:',length(problems),'\n')
print(fit_pairs$coefficients[fit_pairs$coefficients$term=='alert_lag1',])
print(fit_trip$coefficients[grepl('history',fit_trip$coefficients$term),])
print(do.call(rbind,coxrows)[1:3,])
