options(stringsAsFactors=FALSE,scipen=8)
suppressPackageStartupMessages(library(survival))
ROOT<-'__LEGACY_ROOT__'
OUT<-file.path(ROOT,'work/ssi_inferential_stats')
g<-read.csv(file.path(ROOT,'outputs/SSI_Prevention_Intelligence/SSI_Signal_Memory_Vector_Atlas/reproducibility/maximum_time_to_alert_cohort.csv'))
g$severity<-factor(ifelse(g$baseline_cases==0,0,ifelse(g$baseline_cases<=g$baseline_expected,1,ifelse(g$baseline_cases<=2*g$baseline_expected,2,3))),levels=0:3)
g$stratum<-interaction(g$age,g$procedure,g$baseline_year,drop=TRUE)
warnings_log<-character()
fit<-withCallingHandlers(coxph(Surv(time,event)~severity+log1p(baseline_operations)+log1p(baseline_expected)+strata(stratum),
  data=g,ties='efron',cluster=site,robust=TRUE,x=TRUE,control=coxph.control(iter.max=100)),warning=function(w){warnings_log<<-c(warnings_log,conditionMessage(w));invokeRestart('muffleWarning')})
s<-summary(fit);ix<-grep('severity',rownames(s$coefficients));cf<-s$coefficients[ix,,drop=FALSE];ci<-s$conf.int[ix,,drop=FALSE]
rows<-data.frame(comparison=paste0('Severity ',1:3,' versus no baseline SSI'),HR=ci[,'exp(coef)'],lower=ci[,'lower .95'],upper=ci[,'upper .95'],robust_SE=cf[,'robust se'],p=cf[,'Pr(>|z|)'])
rows$q_BH<-p.adjust(rows$p,'BH')
write.csv(rows,file.path(OUT,'four_baseline_states_adjusted_Cox_HR.csv'),row.names=FALSE)
b<-coef(fit)[ix];V<-vcov(fit)[ix,ix];chi<-as.numeric(t(b)%*%solve(V)%*%b)
global<-data.frame(model='Four baseline states proportional Cox',df=3,Wald_chisq=chi,p=pchisq(chi,3,lower.tail=FALSE))
write.csv(global,file.path(OUT,'four_baseline_states_global_tests.csv'),row.names=FALSE)
ph<-cox.zph(fit);tab<-as.data.frame(ph$table);tab$term<-rownames(tab)
write.csv(tab,file.path(OUT,'four_baseline_states_PH_diagnostics.csv'),row.names=FALSE)
for(j in 1:3)g[[paste0('s',j)]]<-as.integer(g$severity==j)
tv<-withCallingHandlers(coxph(Surv(time,event)~s1+s2+s3+tt(s1)+tt(s2)+tt(s3)+log1p(baseline_operations)+log1p(baseline_expected)+strata(stratum),
  data=g,ties='efron',cluster=site,robust=TRUE,tt=function(x,t,...)x*log1p(t),control=coxph.control(iter.max=100)),warning=function(w){warnings_log<<-c(warnings_log,conditionMessage(w));invokeRestart('muffleWarning')})
b<-coef(tv);V<-vcov(tv);time_rows<-list();time_global<-list()
for(t in c(1,3,5,9)) {
  Ls<-matrix(0,3,length(b));colnames(Ls)<-names(b)
  for(j in 1:3) {
    L<-rep(0,length(b));names(L)<-names(b);L[paste0('s',j)]<-1;L[paste0('tt(s',j,')')]<-log1p(t);Ls[j,]<-L
    val<-sum(L*b);se<-sqrt(as.numeric(t(L)%*%V%*%L))
    time_rows[[length(time_rows)+1]]<-data.frame(comparison=paste0('Severity ',j,' versus no baseline SSI'),followup_year=t,HR=exp(val),lower=exp(val-1.96*se),upper=exp(val+1.96*se),p=2*pnorm(abs(val/se),lower.tail=FALSE))
  }
  delta<-Ls%*%b;VV<-Ls%*%V%*%t(Ls);chi<-as.numeric(t(delta)%*%solve(VV)%*%delta)
  time_global[[length(time_global)+1]]<-data.frame(model='Four baseline states time-varying Cox',followup_year=t,df=3,Wald_chisq=chi,p=pchisq(chi,3,lower.tail=FALSE))
}
ttix<-grep('tt',names(b));bb<-b[ttix];vv<-V[ttix,ttix];chi<-as.numeric(t(bb)%*%solve(vv)%*%bb)
time_global[[length(time_global)+1]]<-data.frame(model='Joint severity by log(1 + follow-up time) interaction',followup_year=NA_integer_,df=3,Wald_chisq=chi,p=pchisq(chi,3,lower.tail=FALSE))
z<-do.call(rbind,time_rows);z$q_BH<-NA_real_;for(t in unique(z$followup_year)){ii<-which(z$followup_year==t);z$q_BH[ii]<-p.adjust(z$p[ii],'BH')}
write.csv(z,file.path(OUT,'four_baseline_states_time_varying_Cox_HR.csv'),row.names=FALSE)
write.csv(do.call(rbind,time_global),file.path(OUT,'four_baseline_states_time_varying_global_tests.csv'),row.names=FALSE)
write.csv(aggregate(cbind(units=rep(1,nrow(g)),events=g$event)~severity,g,sum),file.path(OUT,'four_baseline_states_cohort_totals.csv'),row.names=FALSE)
writeLines(if(length(warnings_log))warnings_log else 'None',file.path(OUT,'four_baseline_states_model_warnings.txt'))
print(rows);print(ph$table);print(z)
