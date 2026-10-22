O<-'work/ssi_figure17_redesign/fourpanel_analysis'
m<-read.csv(file.path(O,'profile_ecotypes_and_projection.csv'),stringsAsFactors=FALSE)
d<-read.csv(file.path(O,'profile_depth_counts_long.csv'),stringsAsFactors=FALSE)
a<-read.csv(file.path(O,'later_conditional_mrsa_profiles.csv'),stringsAsFactors=FALSE)
v<-m[m$role=='Later evaluation',]
multilabels<-function(labels){
 labs<-sort(unique(labels));cnt<-as.integer(table(factor(labels,levels=labs)));n<-length(labels);out<-list()
 rec<-function(i,rem,vec){
  if(i==length(labs)){vec[rem]<-labs[i];out[[length(out)+1L]]<<-vec;return(invisible(NULL))}
  choices<-combn(rem,cnt[i],simplify=FALSE)
  for(sel in choices){vv<-vec;vv[sel]<-labs[i];rec(i+1,setdiff(rem,sel),vv)}
 }
 rec(1,seq_len(n),integer(n));do.call(rbind,out)
}
blockedlabels<-function(labels,block){
 bl<-unique(block);aa<-lapply(bl,function(b)multilabels(labels[block==b]));idx<-expand.grid(lapply(aa,function(x)seq_len(nrow(x))));out<-matrix(NA_integer_,nrow(idx),length(labels))
 for(i in seq_len(nrow(idx)))for(j in seq_along(bl))out[i,block==bl[j]]<-aa[[j]][idx[i,j],]
 out
}
fstat<-function(y,age,lab){
 rr<-lm(y~factor(age));ff<-lm(y~factor(age)+factor(lab));s0<-sum(resid(rr)^2);s1<-sum(resid(ff)^2);df0<-df.residual(rr);df1<-df.residual(ff)
 ((s0-s1)/(df0-df1))/(s1/df1)
}
permtest<-function(y,age,lab){
 L<-blockedlabels(lab,age);obs<-fstat(y,age,lab);all<-apply(L,1,function(ll)fstat(y,age,ll));list(F=obs,p=sum(all>=obs-1e-10)/length(all),permutations=length(all),df1=length(unique(lab))-1,df2=length(y)-length(unique(age))-length(unique(lab))+1)
}
# Depth is not used in ecotype learning. Analyze each profile once in later evaluation.
D<-merge(v,d[d$depth=='Organ/space',],by='profile_id',sort=FALSE)
pt<-permtest(D$proportion,D$age,D$ecotype)
print(c(outcome='Organ/space report share',unlist(pt)))
# Source-report Wilson intervals and profile-resampling intervals are kept distinct.
wilson<-function(k,n){z<-qnorm(.975);p<-k/n;de<-1+z*z/n;ce<-(p+z*z/(2*n))/de;ha<-z*sqrt(p*(1-p)/n+z*z/(4*n*n))/de;c(ce-ha,ce+ha)}
set.seed(20261020);B<-9999L
bs<-list()
for(g in sort(unique(D$ecotype))){
 z<-D[D$ecotype==g,];nn<-nrow(z);vv<-replicate(B,{ii<-sample.int(nn,nn,replace=TRUE);sum(z$count[ii])/sum(z$total[ii])});ww<-wilson(sum(z$count),sum(z$total));ci<-quantile(vv,c(.025,.975),names=FALSE)
 bs[[as.character(g)]]<-data.frame(ecotype=g,profiles=nn,source_reports=sum(z$total),organ_space_reports=sum(z$count),organ_space_fraction=sum(z$count)/sum(z$total),source_wilson_lower=ww[1],source_wilson_upper=ww[2],profile_boot_lower=ci[1],profile_boot_upper=ci[2],mean_profile_fraction=mean(z$proportion),median_profile_fraction=median(z$proportion))
}
write.csv(do.call(rbind,bs),file.path(O,'panel_b_later_depth_prevalence.csv'),row.names=FALSE)
write.csv(D,file.path(O,'later_organ_space_profile_values.csv'),row.names=FALSE)
# Independent conditional MRSA percentages were not clustering features.
A<-merge(a,v[,c('profile_id','ecotype')],by='profile_id',sort=FALSE)
pm<-permtest(A$percent_mrsa,A$age,A$ecotype)
print(c(outcome='Conditional MRSA percent',unlist(pm)))
fit<-lm(percent_mrsa~factor(age)+factor(ecotype),data=A)
print(summary(fit));print(confint(fit))
write.csv(A,file.path(O,'panel_d_later_conditional_mrsa_values.csv'),row.names=FALSE)
write.csv(data.frame(term=names(coef(fit)),estimate=coef(fit),lower=confint(fit)[,1],upper=confint(fit)[,2]),file.path(O,'panel_d_age_adjusted_mrsa_effects.csv'),row.names=FALSE)
pair<-A[A$ecotype%in%c(1,2),];pp<-permtest(pair$percent_mrsa,pair$age,pair$ecotype)
print(c(outcome='Conditional MRSA ecotype1vs2',unlist(pp)))
# Clinical depth pairwise exact profile permutation, FDR across 3 pairwise contrasts.
prs<-list();gg<-sort(unique(D$ecotype));ix<-combn(gg,2)
for(j in seq_len(ncol(ix))){
 x<-D[D$ecotype%in%ix[,j],];p<-permtest(x$proportion,x$age,x$ecotype)
 lm1<-lm(proportion~factor(age)+factor(ecotype),data=x);term<-names(coef(lm1))[length(coef(lm1))]
 prs[[j]]<-data.frame(group0=ix[1,j],group1=ix[2,j],adjusted_difference=coef(lm1)[term],t_ci_lower=confint(lm1)[term,1],t_ci_upper=confint(lm1)[term,2],permutation_p=p$p,permutations=p$permutations)
}
pr<-do.call(rbind,prs);pr$BH_q<-p.adjust(pr$permutation_p,'BH');write.csv(pr,file.path(O,'panel_b_pairwise_profile_contrasts.csv'),row.names=FALSE)
write.csv(data.frame(outcome=c('Organ/space report fraction','Conditional MRSA percent','Conditional MRSA percent ecotype1vs2'),F=c(pt$F,pm$F,pp$F),p=c(pt$p,pm$p,pp$p),permutations=c(pt$permutations,pm$permutations,pp$permutations),profiles=c(nrow(D),nrow(A),nrow(pair)),inference='Exact permutation of ecotype labels within age group; profile is unit; age-adjusted partial-F statistic'),file.path(O,'ecological_profile_permutation_tests.csv'),row.names=FALSE)
# Composition heatmap contains defining features. It has no tests against cluster membership.
w<-read.csv(file.path(O,'profile_counts_long.csv'),stringsAsFactors=FALSE);W<-merge(v[,c('profile_id','ecotype')],w,by='profile_id')
h<-aggregate(cbind(count,total)~ecotype+pathogen,data=W,sum);h$proportion<-h$count/h$total;write.csv(h,file.path(O,'panel_c_later_component_heatmap.csv'),row.names=FALSE)
# All three depth outcomes are disclosed; primary family has these3 and independent conditional MRSA.
all_depth_results<-list();all_depth_bars<-list()
for(dep in c('Superficial incisional','Deep incisional','Organ/space')){
 Z<-merge(v,d[d$depth==dep,],by='profile_id',sort=FALSE);ppp<-permtest(Z$proportion,Z$age,Z$ecotype)
 all_depth_results[[dep]]<-data.frame(outcome=dep,F=ppp$F,p=ppp$p,permutations=ppp$permutations,profiles=nrow(Z))
 for(g in sort(unique(Z$ecotype))){
  z<-Z[Z$ecotype==g,];nn<-nrow(z);set.seed(20261020+g);vv<-replicate(B,{ii<-sample.int(nn,nn,replace=TRUE);sum(z$count[ii])/sum(z$total[ii])});ci<-quantile(vv,c(.025,.975),names=FALSE);ww<-wilson(sum(z$count),sum(z$total))
  all_depth_bars[[paste(dep,g)]]<-data.frame(depth=dep,ecotype=g,profiles=nn,source_reports=sum(z$total),depth_reports=sum(z$count),fraction=sum(z$count)/sum(z$total),profile_boot_lower=ci[1],profile_boot_upper=ci[2],source_wilson_lower=ww[1],source_wilson_upper=ww[2])
 }
}
G<-rbind(do.call(rbind,all_depth_results),data.frame(outcome='Conditional MRSA percent',F=pm$F,p=pm$p,permutations=pm$permutations,profiles=nrow(A)));G$BH_q<-p.adjust(G$p,'BH');G$unit<-'Age-procedure source profile';G$test<-'Exact age-blocked profile permutation, partial-F statistic';write.csv(G,file.path(O,'all_independent_outcome_tests_BH_family4.csv'),row.names=FALSE);write.csv(do.call(rbind,all_depth_bars),file.path(O,'panel_b_all_depth_prevalences.csv'),row.names=FALSE)
print(G)
