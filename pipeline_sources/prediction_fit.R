options(stringsAsFactors=FALSE,scipen=8)
OUT<-'__LEGACY_ROOT__/work/ssi_new_prediction'
d<-read.csv(gzfile(file.path(OUT,'lagged_prediction_cohort.csv.gz')))
train<-d[d$set=='Training',];evaluate<-d[d$set!='Training',]
features<-c('log_volume','log_expected_rate','log_prior_sir','log_history_sir')
scales<-data.frame(feature=features,center=NA_real_,scale=NA_real_)
for(j in seq_along(features)){
 f<-features[j];m<-mean(train[[f]]);sdv<-sd(train[[f]])
 train[[paste0(f,'_z')]]<-(train[[f]]-m)/sdv
 evaluate[[paste0(f,'_z')]]<-(evaluate[[f]]-m)/sdv
 scales$center[j]<-m;scales$scale[j]<-sdv
}
for(f in c('procedure','age')){
 train[[f]]<-factor(train[[f]])
 stopifnot(all(evaluate[[f]] %in% levels(train[[f]])))
 evaluate[[f]]<-factor(evaluate[[f]],levels=levels(train[[f]]))
}
warns<-character()
fit<-withCallingHandlers(glm(outcome~age+procedure+log_volume_z+log_expected_rate_z+
 log_prior_sir_z+log_history_sir_z,data=train,family=binomial(),control=glm.control(maxit=100)),warning=function(w){warns<<-c(warns,conditionMessage(w));invokeRestart('muffleWarning')})
stopifnot(fit$converged,all(is.finite(coef(fit))))
evaluate$combined<-as.numeric(predict(fit,newdata=evaluate,type='response'))
stopifnot(all(is.finite(evaluate$combined)),all(evaluate$combined>0 & evaluate$combined<1))
for(f in c('prior_volume','prior_cases','prior_sir','combined'))evaluate[[f]]<-signif(evaluate[[f]],12)
write.csv(evaluate,file.path(OUT,'heldout_predictions.csv'),row.names=FALSE)
write.csv(scales,file.path(OUT,'training_feature_scaling.csv'),row.names=FALSE)
cf<-summary(fit)$coefficients
write.csv(data.frame(term=rownames(cf),estimate=cf[,1],SE=cf[,2],p=cf[,4]),file.path(OUT,'model_coefficients.csv'),row.names=FALSE)
saveRDS(fit,file.path(OUT,'report_alert_model.rds'))
writeLines(c(paste('Converged:',fit$converged),paste('Iterations:',fit$iter),paste('Rank:',fit$rank),paste('Coefficients:',length(coef(fit))),paste('Warnings:',if(length(warns))paste(warns,collapse='; ')else'None'),paste('Training:',nrow(train)),paste('Training alerts:',sum(train$outcome)),paste('Evaluation:',nrow(evaluate)),paste('Prediction range:',paste(range(evaluate$combined),collapse=' to '))),file.path(OUT,'model_fit_audit.txt'))
print(summary(fit))
