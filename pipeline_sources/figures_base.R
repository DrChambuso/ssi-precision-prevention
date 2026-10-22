options(stringsAsFactors=FALSE,scipen=6)
library(survival)
B<-"__LEGACY_ROOT__/outputs/SSI_Prevention_Intelligence/SSI_Inferential_Microbiology_Figures"
T<-file.path(B,"tables");P<-file.path(B,"individual_vector_pdfs")
N<-file.path(B,"reproducibility/prediction")
d<-read.csv(gzfile(file.path(B,"reproducibility/annual_reports.csv.gz")))
pa<-d[!is.na(d$alert_lag1),];tr<-d[!is.na(d$alert_lag1)&!is.na(d$alert_lag2),]
tr$history<-paste0(tr$alert_lag2,tr$alert_lag1)
s<-read.csv(file.path(T,"population_and_procedure_profiles.csv"))
pr<-s[s$kind=="Procedure",]; key<-read.csv(file.path(T,"procedure_key.csv"))
an<-read.csv(file.path(T,"annual_procedure_profiles.csv"))
aa<-read.csv(file.path(T,"age_annual_procedure_rates.csv"))
hi<-read.csv(file.path(T,"two_year_signal_memory.csv"),colClasses=c(history="character"))
co<-read.csv(file.path(B,"reproducibility/maximum_time_to_alert_cohort.csv"))
u<-read.csv(file.path(T,"ranked_units.csv"))
cells<-read.csv(gzfile(file.path(T,"report_history_cells.csv.gz")))
pred<-read.csv(file.path(N,"heldout_predictions.csv"))
perf<-read.csv(file.path(N,"heldout_performance.csv"))
cur<-read.csv(gzfile(file.path(N,"ROC_PR_curve_coordinates.csv.gz")))
cap<-read.csv(file.path(N,"review_capacity_results.csv"))
cc<-read.csv(file.path(N,"review_capacity_curve.csv"))
cal<-read.csv(file.path(N,"calibration_deciles.csv"))
top<-names(sort(tapply(d$y[d$year<=2022],d$procedure[d$year<=2022],sum),decreasing=TRUE))[1:8]

ST<-file.path(T,"statistics")
rd<-function(f)read.csv(file.path(ST,f))
FS<-rd("family_prior_signal_associations.csv");PRR<-rd("procedure_prior_alert_adjusted_RR.csv")
TRN<-rd("procedure_annual_trend_adjusted_IRR.csv");EL<-rd("procedure_early_late_adjusted_IRR.csv")
TV<-rd("time_varying_high_baseline_HR.csv");SEV<-rd("four_baseline_states_time_varying_Cox_HR.csv")
SEVG<-rd("four_baseline_states_time_varying_global_tests.csv");GW<-rd("all_site_robust_global_Wald_tests.csv")
PC<-rd("prediction_paired_comparisons_1999_cluster_bootstrap.csv")
CJ<-rd("prediction_calibration_joint_test.csv");CAL<-rd("prediction_calibration_site_robust.csv")
MEM<-rd("two_year_memory_contrasts.csv");STD<-rd("two_year_memory_logistic_standardized_probabilities.csv")
EAR<-rd("earlier_service_context_standardized_contrasts.csv")
CASE<-rd("future_SSI_case_capture_comparisons.csv")
PM<-rd("prediction_metrics_1999_cluster_bootstrap.csv");for(i in 1:nrow(perf)){for(mt in c("AUC","AP")){r<-PM[PM$dataset==perf$dataset[i]&PM$group==perf$group[i]&PM$method==perf$method[i]&PM$metric==mt,];if(nrow(r)){perf[i,paste0(mt,"_lower")]<-r$lower[1];perf[i,paste0(mt,"_upper")]<-r$upper[1]}}}
XD<-read.csv(file.path(T,"microbiology/california_28_procedure_microbiology_context_crosswalk.csv"))
pstr<-function(x)if(!length(x)||!is.finite(x[1]))"NE" else if(x[1]<.001)"<0.001"else paste0("=",sprintf("%.3f",x[1]))
est<-function(r,type="aRR",q=FALSE){if(!nrow(r))return("Adjusted estimate not estimable");paste0(type," ",sprintf("%.2f (%.2f-%.2f)",r$effect[1],r$lower[1],r$upper[1]),"; ",if(q)"q"else"P",pstr(if(q)r$q_BH else r$p))}
fs<-function(group,outcome){FS[FS$group==group&FS$outcome==outcome,]}
procRR<-function(p){PRR[PRR$procedure==p,]}
trend<-function(p){TRN[TRN$procedure==p,]}
paired<-function(dataset="Test",group="All ages and procedures",metric="AUC"){PC[PC$dataset==dataset&PC$group==group&PC$metric==metric&PC$comparator=="prior_cases",]}
tv<-function(group,year){TV[TV$group==group&TV$followup_year==year,]}
predline<-function(r,metric="AUC"){if(!nrow(r))return("Comparison not estimable");paste0("Added ",metric," ",sprintf("%+.3f (%.3f-%.3f)",r$difference[1],r$lower[1],r$upper[1]),"; P",pstr(r$p_centered_bootstrap[1]),if(is.finite(r$q_BH[1]))paste0("; BH q",pstr(r$q_BH[1]))else "") }
foresttable<-function(z,title,xlabel="Adjusted risk ratio (95% CI)",xlim=c(.5,4),labels=NULL){
 par(mar=c(4.7,11,3,6),cex=.88,xpd=FALSE)
 if(is.null(labels))labels<-z$label
 plot(0,0,type="n",log="x",xlim=xlim,ylim=c(.5,nrow(z)+.7),yaxt="n",xlab=xlabel,ylab="",main=title,cex.main=.95)
 abline(v=1,col=GREY,lty=2)
 for(i in 1:nrow(z)){yy<-nrow(z)+1-i;ci(z$effect[i],z$lower[i],z$upper[i],yy,col=if("color"%in%names(z))z$color[i]else BLUE);text(xlim[1]*.94,yy,labels[i],adj=1,cex=.74,xpd=NA);text(xlim[2]*1.05,yy,paste0(sprintf("%.2f (%.2f-%.2f)",z$effect[i],z$lower[i],z$upper[i]),"\n",if("q"%in%names(z))paste0("q",pstr(z$q[i]))else paste0("P",pstr(z$p[i]))),adj=0,cex=.68,xpd=NA)}
}

BLUE<-"#2476B5";RED<-"#CE2635";GREEN<-"#229B86";ORANGE<-"#ED7800";PURPLE<-"#7956A8";GOLD<-"#CDA400"
GREY<-"#636363";LIGHT<-"#F1F3F5";INK<-"#162332"
cols<-c(BLUE,RED,GREEN,ORANGE,PURPLE,GOLD)
statecol<-c("#A6CEE3",BLUE,PURPLE,"#B50010")
histcol<-c(GREEN,ORANGE,BLUE,RED)
fmt<-function(x)format(round(x),big.mark=",",scientific=FALSE,trim=TRUE)
lab<-function(x)key$label[match(x,key$procedure)]
ce<-function(x,digits=1)formatC(x,format="f",digits=digits)
fpath<-function(i,name)file.path(P,sprintf("Figure_%02d_%s.pdf",i,name))
openpdf<-function(i,name,w=14,h=9){pdf(fpath(i,name),width=w,height=h,family="Helvetica",useDingbats=FALSE);par(family="Helvetica",fg=INK,col=INK,col.axis=INK,col.lab=INK,bty="l",las=1,mgp=c(2.3,.65,0),tcl=-.2)}
headfoot<-function(title,note){mtext(title,side=3,outer=TRUE,line=.65,adj=0,font=2,cex=1.1);mtext(note,side=1,outer=TRUE,line=.7,adj=0,cex=.65)}
letter<-function(x) mtext(x,side=3,line=.3,adj=0,font=2,cex=1.2)
ci<-function(x,l,u,y,col=BLUE){segments(l,y,u,y,col=col,lwd=1);segments(l,y-.07,l,y+.07,col=col);segments(u,y-.07,u,y+.07,col=col);points(x,y,pch=16,col=col,cex=.75)}
empty<-function(xlim=c(0,1),ylim=c(0,1)){plot.new();plot.window(xlim=xlim,ylim=ylim,xaxs="i",yaxs="i")}
qtab<-function(g,metric,ticks,y=-.24){
 text(-.01,y+.075,"Reports at or below threshold",adj=0,cex=.51,font=2,xpd=NA)
 for(j in seq_along(ticks))text((j-1)/(length(ticks)-1),y,fmt(ticks[j]),cex=.52,xpd=NA)
 for(k in 0:1){v<-g[g$alert==k,metric];for(j in seq_along(ticks))text((j-1)/(length(ticks)-1),y-.07*(k+1),fmt(sum(v<=ticks[j])),col=c(BLUE,RED)[k+1],cex=.5,xpd=NA)}
}
ecdfpanel<-function(g,metric,title,L,kind="signal"){
 par(mar=c(6.2,4.2,2.2,.7),cex=.82)
 v<-g[[metric]]; ticks<-if(metric=="n")c(1,10,100,1000,10000)else c(0,1,5,20,100,1000)
 xmax<-max(v,na.rm=TRUE);xt<-sort(unique(c(ticks[ticks<=xmax],xmax)))
 plot(0,0,type="n",xlim=c(0,log1p(xmax)),ylim=c(0,1),axes=FALSE,xlab=if(metric=="n")"Operations per annual report"else"SSIs per 1,000 operations",ylab="Cumulative percentage of reports",main=title,cex.main=.9)
 for(k in 0:1){z<-sort(g[g$alert_lag1==k,metric]);lines(log1p(z),seq_along(z)/length(z),type="s",col=c(BLUE,RED)[k+1],lty=k+1,lwd=1.2)}
 axis(1,log1p(xt),fmt(xt),cex.axis=.65);axis(2,seq(0,1,.25),seq(0,100,25),cex.axis=.7);box(bty="l")
 legend("bottomright",legend=sprintf(c("Prior at/below (n=%s)","Prior above (n=%s)"),fmt(c(sum(g$alert_lag1==0),sum(g$alert_lag1==1)))),col=c(BLUE,RED),lty=1:2,bty="n",cex=.57)
 gg<-strsplit(title," - ",fixed=TRUE)[[1]][1];if(gg=="All procedures")gg<-"All ages and procedures";rr<-fs(gg,if(metric=="n")"Geometric mean of operations plus 1"else"SSI rate");mtext(est(rr,if(metric=="n")"Workload ratio"else"aIRR"),3,line=.1,adj=0,cex=.62);letter(L)
 # A compact count table uses the plotting coordinates with a visible threshold caption.
 yy<-par("usr");xx<-log1p(ticks[ticks<=xmax]);tk<-ticks[ticks<=xmax]
 mtext("Counts at/below threshold; unevenly spaced horizontal axis",side=1,line=3.5,cex=.53)
 for(k in 0:1)mtext(sapply(tk,function(t)sum(g[g$alert_lag1==k,metric]<=t)),side=1,line=4.45+.8*k,at=xx,col=c(BLUE,RED)[k+1],cex=.51)
}

# 01. Same cumulative-curve presentation as the first supplied example.
openpdf(1,"cumulative_report_workload_and_SSI_burden",14,14)
par(mfrow=c(5,2),oma=c(2.2,.4,2.1,.5))
families<-c("All procedures",sort(unique(d$family)))
for(i in 1:5){g<-if(i==1)pa else pa[pa$family==families[i],];ecdfpanel(g,"n",paste(families[i],"- report workload"),LETTERS[2*i-1]);ecdfpanel(g,"rate",paste(families[i],"- SSI burden"),LETTERS[2*i])}
headfoot("Does an earlier SSI signal identify a larger following-year SSI burden?","57,485 consecutive report comparisons. Groups use the previous report. Adjusted following-year effects use hospital-cluster robust inference; SSI counts use operation offsets.")
dev.off()

kmres<-list()
km<-function(g,name,group="high"){
 g$z<-factor(g[[group]])
 fit<-survfit(Surv(time,event)~z,data=g,cluster=site,robust=TRUE,conf.type="log-log",time0=TRUE)
 ss<-summary(fit,times=5,extend=TRUE)
 tab<-summary(fit)$table
 out<-data.frame(analysis=name,group=levels(g$z),units=as.numeric(table(g$z)),alerts=as.numeric(tapply(g$event,g$z,sum)),S5=ss$surv,lo=ss$lower,hi=ss$upper,median=tab[,"median"])
 kmres[[name]]<<-out
 list(data=g,fit=fit,table=out,name=name)
}
kmplot<-function(z,title,L,colors=c(BLUE,RED),groups=c("Baseline at/below predicted","Baseline above predicted"),risk=TRUE){
 par(mar=c(if(risk)6.1 else 4.2,4.5,2.5,.9),cex=.86)
 plot(z$fit,col=colors,lty=2,lwd=1.5,mark.time=TRUE,pch=1,cex=.3,conf.int=FALSE,axes=FALSE,xlim=c(0,9),ylim=c(0,1),xlab="Years from first eligible baseline report",ylab="Units without a follow-up SSI signal (%)",main=title,cex.main=1)
 axis(1,0:9);axis(2,seq(0,1,.2),seq(0,100,20));box(bty="l");letter(L);if(z$name%in%c("Adult","Pediatric")){r1<-tv(z$name,1);r5<-tv(z$name,5);legend("topright",c("Time-varying adjusted HR (95% CI)",paste0("Year 1: ",sprintf("%.2f (%.2f-%.2f)",r1$HR,r1$lower,r1$upper),"; P",pstr(r1$p)),paste0("Year 5: ",sprintf("%.2f (%.2f-%.2f)",r5$HR,r5$lower,r5$upper),"; P",pstr(r5$p))),bty="n",cex=.69)}
 legend("bottomleft",legend=paste0(groups," (n=",fmt(z$table$units),")"),col=colors,lty=2,bty="n",cex=.68)
 if(risk){mtext("Number at risk",1,line=3.1,adj=0,font=2,cex=.65);tt<-c(0,2,4,6,9)
  for(k in seq_along(levels(z$data$z))){g<-z$data[z$data$z==levels(z$data$z)[k],];mtext(sapply(tt,function(t)sum(g$time>=t)),1,line=3.8+.7*k,at=tt,col=colors[k],cex=.63)}}
}
# 02. Two KM panels above a source-backed summary table, as example 2.
openpdf(2,"followup_signal_survival_and_summary",14,10)
layout(matrix(c(1,2,3,3),2,2,byrow=TRUE),heights=c(3,1.7));par(oma=c(2,.5,2,.5))
for(i in 1:2){g<-co[co$age==c("Adult","Pediatric")[i],];z<-km(g,c("Adult","Pediatric")[i]);kmplot(z,paste(c("Adult","Pediatric")[i],"time to next SSI signal"),LETTERS[i])}
par(mar=c(0,0,1,0));empty(c(0,1),c(0,10));text(.01,9.6,"Five-year follow-up signal summary",adj=0,font=2)
xx<-c(.01,.39,.52,.65,.80,.96);heads<-c("Population or procedure","Units","First signals","At/below baseline:\n5-yr signal-free % (95% CI)","Above baseline:\n5-yr signal-free % (95% CI)","Follow-up\nSSI cases")
for(j in 1:6)text(xx[j],8.5,heads[j],adj=if(j==1)0 else .5,cex=.65,font=2)
tabgroups<-c("All ages",top[1:6]);for(i in seq_along(tabgroups)){g<-if(i==1)co else co[co$procedure==tabgroups[i],];z<-km(g,paste0("Summary ",tabgroups[i]));yy<-7.7-(i-1)*.95;if(i%%2)rect(0,yy-.4,1,yy+.4,col=LIGHT,border=NA);vv<-c(if(i==1)tabgroups[i]else lab(tabgroups[i]),fmt(nrow(g)),fmt(sum(g$event)),sprintf("%.1f (%.1f-%.1f)",100*z$table$S5[1],100*z$table$lo[1],100*z$table$hi[1]),sprintf("%.1f (%.1f-%.1f)",100*z$table$S5[2],100*z$table$lo[2],100*z$table$hi[2]),fmt(sum(g$followup_SSI_cases)));for(j in 1:6)text(xx[j],yy,vv[j],adj=if(j==1)0 else .5,cex=.68)}
headfoot("How long do earlier SSI signals remain relevant to prevention review?","All 10,081 eligible units, 4,191 first follow-up signals. Annual reporting times; follow-up stops at the first missing year. Hospitals define CI clusters.");dev.off()

# 03. Full-population vector oncoprint, not a sample of units.
openpdf(3,"ranked_temporal_SSI_signal_oncoprint",15,10)
par(oma=c(2.1,.2,2,.3));layout(matrix(1:6,3,2,byrow=TRUE),widths=c(4.3,1.25),heights=c(1.15,3.8,1.3))
par(mar=c(.1,7,.3,.3));plot(seq_len(nrow(u)),100*u$alert_fraction,type="s",col=BLUE,lwd=.8,axes=FALSE,xlab="",ylab="Signal reports (%)",ylim=c(0,100),xaxs="i");axis(2,c(0,50,100));box(bty="l");mtext("A",3,line=-.5,adj=0,font=2)
par(mar=c(.1,0,.3,1));empty();text(0,.85,"Complete report history",adj=0,font=2,cex=.85);text(0,.57,"12,507 units; 72,854 reports\n6,737,972 operations",adj=0,cex=.75);r<-fs("All ages and procedures","Annual report alert");text(0,.19,paste0("Independent next-report comparison\n",est(r)),adj=0,cex=.67)
par(mar=c(.2,7,.2,.3));empty(c(0,nrow(u)),c(.5,10.5));rect(0,.5,nrow(u),10.5,col="#ECECEC",border=NA)
for(yr in 2016:2025){v<-cells[cells$year==yr,];y<-2026-yr;rect(v$column,y-.43,v$column+1,y+.43,col=ifelse(v$alert,RED,GREY),border=NA)}
axis(2,10:1,2016:2025,tick=FALSE);mtext("B",2,line=3.3,at=10,cex=.9,font=2,las=1)
par(mar=c(.2,0,.2,1));empty(c(0,8500),c(.5,10.5));for(yr in 2016:2025){g<-d[d$year==yr,];yy<-2026-yr;tot<-nrow(g);nalert<-sum(g$alert);rect(0,yy-.29,nalert,yy+.29,col=RED,border=NA);rect(nalert,yy-.29,tot,yy+.29,col=GREY,border=NA);text(8450,yy,fmt(tot),adj=1,cex=.62)};mtext("Annual composition (reports)",3,line=.2,cex=.75)
par(mar=c(4.3,7,.6,.3));empty(c(0,nrow(u)),c(0,4));flev<-sort(unique(u$family));fc<-setNames(c(BLUE,GREEN,ORANGE,PURPLE),flev)
trackcols<-list(ifelse(u$age=="Adult",BLUE,ORANGE),fc[u$family],colorRampPalette(c("#D7EEF1",GREEN))(10)[pmin(10,u$reports)],colorRampPalette(c("#E4EDF6","#12446A"))(6)[pmin(6,1+floor(log10(u$operations)))])
for(i in 1:4)rect(0:(nrow(u)-1),4-i,1:nrow(u),4-i+.75,col=trackcols[[i]],border=NA)
axis(2,c(3.375,2.375,1.375,.375),c("Age group","Procedure family","Observed years","Operation volume"),tick=FALSE,cex.axis=.72)
axis(1,c(1,2500,5000,7500,10000,12507),fmt(c(1,2500,5000,7500,10000,12507)),cex.axis=.7);mtext("Hospital-age-procedure units ranked by fraction of reports above predicted",1,2.2,cex=.8)
par(mar=c(.2,0,0,0));empty();legend(0,1,c("Above predicted","At/below predicted","Missing report year","Adult","Pediatric",flev),fill=c(RED,GREY,"#ECECEC",BLUE,ORANGE,fc),cex=.75,bty="n",y.intersp=.75);text(.02,.03,"Darker tracks: more observed years (1-10)\nand operations (log10 bins, 1 to >=100,000).",adj=0,cex=.62)
headfoot("Is SSI signal burden isolated, recurrent, or interrupted by reporting gaps?","All 12,507 units and all 72,854 observed reports. Grey = at/below predicted; red = above predicted; pale = missing. No missing years are imputed.");dev.off()

# 04. Exact additive burden decomposition matching the bed-day table style.
openpdf(4,"SSI_burden_by_reporting_pathway",15,12)
par(oma=c(3,.2,2,.2),mar=c(5,1,1,1));empty(c(0,1),c(0,34))
rows<-rbind(s[s$kind=="Population",],pr[order(pr$rate,decreasing=TRUE),]);maxrate<-max(rows$rate,1000*rows$expected/rows$operations)*1.05
text(.01,33.1,"Population or procedure",adj=0,font=2,cex=.8);text(.28,33.1,"Operations",font=2,cex=.8);text(.38,33.1,"SSIs",font=2,cex=.8);text(.88,33.1,"Next-year signal aRR\n(95% CI)",font=2,cex=.74);text(.99,33.1,"P / BH q",adj=1,font=2,cex=.74)
for(i in 1:nrow(rows)){r<-rows[i,];yy<-32-i;if(i%%2)rect(0,yy-.43,1,yy+.43,col=LIGHT,border=NA);text(.01,yy,if(r$kind=="Procedure")lab(r$name)else r$name,adj=0,cex=.69);text(.28,yy,fmt(r$operations),cex=.66);text(.38,yy,fmt(r$cases),cex=.66);v<-as.numeric(r[paste0("state",0:3,"_cases")])*1000/r$operations;cum<-c(0,cumsum(v));for(j in 1:4)rect(.43+.34*cum[j]/maxrate,yy-.24,.43+.34*cum[j+1]/maxrate,yy+.24,col=statecol[j],border=NA);px<-.43+.34*(r$expected*1000/r$operations)/maxrate;segments(px,yy-.3,px,yy+.3,lwd=2);rr<-if(r$kind=="Procedure")procRR(r$name)else if(r$name=="All ages")fs("All ages and procedures","Annual report alert")else data.frame();text(.88,yy,if(nrow(rr))sprintf("%.2f (%.2f-%.2f)",rr$effect,rr$lower,rr$upper)else "NE",cex=.64);text(.99,yy,if(nrow(rr))pstr(if(r$kind=="Procedure")rr$q_BH else rr$p)else "NE",adj=1,cex=.64)}
ax<-pretty(c(0,maxrate),5);ax<-ax[ax<=maxrate];axis(1,.43+.34*ax/maxrate,ax,cex.axis=.7);mtext("Observed SSIs per 1,000 operations, decomposed by current and previous annual reports",1,2.4,cex=.8)
legend(.01,-2.3,c("Current report at/below predicted","Above after prior at/below","Above in two consecutive years","Above with prior year unavailable"),fill=statecol,ncol=2,bty="n",cex=.72,xpd=NA);mtext("Black marker = source-predicted SSI rate. Components sum exactly to observed SSI rate. Right columns: adjusted next-year signal RR; all-age P and 28-procedure BH q. NE = sparse adjusted estimate.",1,outer=TRUE,line=.5,cex=.65,adj=0)
mtext("Where does observed SSI burden coincide with adjusted future-signal association?",3,outer=TRUE,line=.6,font=2,cex=1.1,adj=0);dev.off()

# 05. Dendrogram + evidence columns + annual signal matrix.
feat<-cbind(pr$rate,pr$oe,pr$alert_pct,pr$next_after1_pct,pr$persistent_case_pct)
feat[!is.finite(feat)]<-0;hc<-hclust(dist(scale(feat)),method="average");ord<-hc$order
write.csv(data.frame(order=1:28,procedure=pr$name[ord],cluster=cutree(hc,4)[ord]),file.path(T,"procedure_cluster_order.csv"),row.names=FALSE)
openpdf(5,"hierarchical_procedure_signal_profiles",16,11)
par(oma=c(3,.2,2,.2));layout(matrix(c(1,2),1,2),widths=c(1.5,7));par(mar=c(1,0,3,0));plot(as.dendrogram(hc),horiz=TRUE,leaflab="none",axes=FALSE,xlab="",ylab="",main="");mtext("A  Profile similarity",3,line=1,cex=.8,font=2)
par(mar=c(1,0,3,0));empty(c(0,1),c(.5,29.5));xs<-c(.01,.23,.31,.39,.47,.55);heads<-c("Procedure","Operations","SSIs / 1,000","Observed /\npredicted","Signal\nreports, %","Next signal aRR\n(95% CI), BH q")
for(j in 1:6)text(xs[j],29,heads[j],adj=if(j==1)0 else .5,font=2,cex=.61)
for(i in 1:28){r<-pr[ord[i],];yy<-i;if(i%%2)rect(0,yy-.42,1,yy+.42,col=LIGHT,border=NA);vals<-c(lab(r$name),fmt(r$operations),ce(r$rate),ce(r$oe,2),ce(r$alert_pct),{rr<-procRR(r$name);if(nrow(rr))paste0(sprintf("%.2f (%.2f-%.2f)",rr$effect,rr$lower,rr$upper),"; ",pstr(rr$q_BH))else "NE"});for(j in 1:6)text(xs[j],yy,vals[j],adj=if(j==1)0 else .5,cex=.56);for(k in 1:10){a<-an[an$procedure==r$name&an$year==2015+k,];x<-.62+(k-1)*.037;v<-a$oe;cl<-if(v<=.75)"#B6D8EC"else if(v<=1)"#DBEAF4"else if(v<=1.25)"#EAB9B9"else"#B81F32";rect(x,yy-.29,x+.028,yy+.29,col=cl,border=NA);if(a$alert_pct>=25)points(x+.014,yy,pch=8,cex=.5,col=INK)}}
for(k in 1:10)text(.634+(k-1)*.037,29,2015+k,srt=90,cex=.65)
mtext("B  Procedure evidence and calendar-year observed/predicted profile",3,line=1,adj=0,font=2,cex=.8)
headfoot("Do procedures share recurrent surveillance patterns that could support joint prevention review?","All 28 procedures and 72,854 reports. Clustering is descriptive; the aRR tests a separately defined next-year outcome with hospital-cluster inference and 28-test BH correction. Annual cells: <=0.75, 0.75-1, 1-1.25, >1.25; star = >=25% signal reports.");dev.off()

# 06. Eight procedure cards, matching the multi-tier bar presentation.
openpdf(6,"procedure_prevention_review_cards",15,14)
par(mfrow=c(4,2),oma=c(2.5,.5,2,.5))
for(i in 1:8){r<-pr[pr$name==top[i],];g<-an[an$procedure==top[i],];par(mar=c(3.4,8.2,2.6,4),cex=.8,xpd=NA);empty(c(0,65),c(0,15));mtext(paste(LETTERS[i],lab(top[i])),3,line=.65,adj=-.25,font=2,cex=.9);mtext(paste0("Operations=",fmt(r$operations),"; SSIs=",fmt(r$cases)),3,line=-.25,adj=1,cex=.59);mtext(est(trend(top[i]),"aIRR/year",TRUE),3,line=-1.05,adj=1,cex=.58);mtext(est(procRR(top[i]),"Next-year aRR",TRUE),1,line=2.9,adj=0,cex=.58)
 vals<-c(r$rate,1000*r$expected/r$operations,1000*r$state2_cases/r$operations);lbl<-c("Observed SSI rate","Predicted SSI rate","Repeat-signal SSI rate");topmax<-max(vals)*1.2
 for(j in 1:3){yy<-14-j;rect(0,yy-.27,42,yy+.27,col=LIGHT,border=NA);rect(0,yy-.27,42*vals[j]/topmax,yy+.27,col=c(BLUE,GREY,PURPLE)[j],border=NA);text(-1.5,yy,lbl[j],adj=1,cex=.65);text(44,yy,paste0(ce(vals[j])," / 1,000"),adj=0,cex=.62)}
 tk<-pretty(c(0,topmax),3);tk<-tk[tk<=topmax];text(42*tk/topmax,10.35,ce(tk),cex=.50);text(-1.5,10.35,"Rate per 1,000",adj=1,cex=.55);text(-1.5,9.6,"Signal reports (%)",adj=1,font=2,cex=.65)
 for(j in 1:nrow(g)){yy<-9-(j-1)*.82;rect(0,yy-.22,60,yy+.22,col=LIGHT,border=NA);rect(0,yy-.22,g$alert_pct[j],yy+.22,col=if(g$year[j]<=2022)BLUE else ORANGE,border=NA);ci(g$alert_pct[j],g$alert_lo[j],g$alert_hi[j],yy,col=INK);text(-1.5,yy,g$year[j],adj=1,cex=.65);text(63,yy,paste0(ce(g$alert_pct[j]),"%"),adj=0,cex=.62)}
 axis(1,c(0,20,40,60));mtext("Annual reports above source-predicted SSI count (%)",1,2,cex=.65)}
headfoot("What should each procedure's prevention team monitor?","Top eight procedures chosen by 2016-2022 SSI burden. All years and both age groups retained. Whiskers = 95% hospital-cluster bootstrap intervals.");dev.off()

# 07. Signal transition matrices by procedure family.
openpdf(7,"annual_signal_transition_matrices",14,10)
par(mfrow=c(2,3),oma=c(2,.5,2,.5));fg<-c("All procedures",sort(unique(d$family)))
for(i in 1:5){g<-if(i==1)pa else pa[pa$family==fg[i],];par(mar=c(4.5,5.5,3,1));empty(c(0,2),c(0,2));for(a in 0:1){v<-g[g$alert_lag1==a,];for(b in 0:1){n<-sum(v$alert==b);pc<-100*n/nrow(v);rect(b,1-a,b+1,2-a,col=if(b==1)colorRampPalette(c("#F9EEEE",RED))(101)[1+round(pc)]else colorRampPalette(c("#F0F5F8",BLUE))(101)[1+round(pc)],border="white",lwd=2);text(b+.5,1.55-a,paste0(ce(pc),"%"),font=2,cex=1.2);text(b+.5,1.25-a,paste0(fmt(n)," / ",fmt(nrow(v))),cex=.7)}};axis(1,c(.5,1.5),c("At/below","Above"),tick=FALSE);axis(2,c(1.5,.5),c("Prior at/below","Prior above"),tick=FALSE,las=1,cex.axis=.7);title(main=paste(LETTERS[i],fg[i]),cex.main=.95,xlab="Following annual report",ylab="");mtext(paste0(fmt(nrow(g))," consecutive comparisons"),3,line=.2,cex=.65);rr<-fs(if(i==1)"All ages and procedures"else fg[i],"Annual report alert");mtext(est(rr,"aRR",i!=1),1,line=3.6,adj=0,cex=.65)}
par(mar=c(0,0,0,0));empty();text(0,.85,"A repeated signal identifies a larger review priority",adj=0,font=2,cex=.9);text(0,.57,"Following report above predicted:\n40.4% after an earlier signal\n12.8% after an at/below-predicted report",adj=0,cex=.9);text(0,.22,"Every comparison uses adjacent calendar years.\nOperations remain SSI incidence denominators.",adj=0,cex=.72)
headfoot("Does a previous annual SSI signal predict recurrence?","All 57,485 consecutive comparisons; 5,711,060 following-year operations and 32,203 SSIs. Cell percentages are conditional on the prior report.");dev.off()

# 08. Four baseline states with number-at-risk and event-free confidence table.
co$severity<-ifelse(co$baseline_cases==0,0,ifelse(co$baseline_cases<=co$baseline_expected,1,ifelse(co$baseline_cases<=2*co$baseline_expected,2,3)))
z<-km(co,"Four baseline signal states","severity")
openpdf(8,"baseline_signal_gradient_time_to_alert",14,9.5)
layout(matrix(c(1,2),2),heights=c(4,1.3));par(oma=c(2,.4,2,.4));kmplot(z,"Time to first follow-up SSI signal","A",histcol,c("No baseline SSI","Baseline SSI at/below predicted","Above predicted, <=2x predicted","Above predicted, >2x predicted"),risk=FALSE)
abline(v=c(2,5),lty=3,col="#999999");vv<-SEV[SEV$followup_year==1,];gg<-SEVG[SEVG$followup_year==1,];legend("topright",c(paste0("Baseline states, year 1 global P",pstr(gg$p)),paste0("State ",1:3," vs no baseline SSI: aHR ",sprintf("%.2f (%.2f-%.2f)",vv$HR,vv$lower,vv$upper),"; q",sapply(vv$q_BH,pstr))),bty="n",cex=.74);par(mar=c(0,1,0,1));empty(c(0,1),c(0,6));tt<-c(0,2,4,6,9);for(j in 1:5)text(.45+(j-1)*.12,5.6,paste0(tt[j]," yr"),font=2,cex=.75)
for(k in 1:4){g<-z$data[z$data$z==levels(z$data$z)[k],];yy<-5-k;text(.01,yy,c("No baseline SSI","SSI at/below predicted","Above, <=2x predicted","Above, >2x predicted")[k],adj=0,col=histcol[k],font=2,cex=.72);for(j in 1:5)text(.45+(j-1)*.12,yy,fmt(sum(g$time>=tt[j])),col=histcol[k],cex=.72)}
text(.01,.1,"All four groups: 10,081 units. A positive SSI count with zero predicted belongs to the >2x count-comparison group.",adj=0,cex=.65)
headfoot("Does a stronger baseline signal shorten the time to another SSI signal?","One entry per hospital-age-procedure unit. Annual follow-up stops at first missing year or 2025. Tables give hospital-unit counts at risk.");dev.off()

# Helpers for held-out prediction curves.
methods<-c("prior_volume","prior_cases","prior_sir","combined")
mcols<-c(BLUE,ORANGE,PURPLE,"black");mlabs<-c("Prior operation volume","Prior SSI count","Prior observed/predicted","Combined report model")
curveplot<-function(dataset,group,title,L,type="ROC"){
 par(mar=c(4.8,4.4,2.7,.7),cex=.83)
 plot(0,0,type="n",xlim=c(0,1),ylim=c(0,1),xlab=if(type=="ROC")"False alert rate"else"Fraction of future signals identified",ylab=if(type=="ROC")"True alert rate"else"Signals among reviewed reports",main=title,cex.main=.9);letter(L)
 if(type=="ROC")abline(0,1,lty=2,col="#A0A0A0")
 labels<-character();for(j in 1:4){v<-cur[cur$dataset==dataset&cur$group==group&cur$method==methods[j],];if(type=="ROC")lines(v$FPR,v$TPR,col=mcols[j],lwd=if(j==4)1.8 else 1.1,lty=c(1,2,3,1)[j])else lines(v$recall,v$precision,col=mcols[j],lwd=if(j==4)1.8 else 1.1,lty=c(1,2,3,1)[j]);r<-perf[perf$dataset==dataset&perf$group==group&perf$method==methods[j],];labels[j]<-paste0(mlabs[j],if(type=="ROC")"  AUC "else"  AP ",ce(if(type=="ROC")r$AUC else r$AP,3))};rr<-paired(dataset,group,if(type=="ROC")"AUC"else"AP");mtext(predline(rr,if(type=="ROC")"AUC"else"AP"),1,line=3.1,adj=0,cex=.54);r0<-perf[perf$dataset==dataset&perf$group==group&perf$method=="combined",];mtext(paste0("Reports=",fmt(r0$reports),"; signals=",fmt(r0$alerts)),3,line=.15,adj=1,cex=.53);if(type=="ROC")labels[4]<-paste0(labels[4]," (",ce(r0$AUC_lower,3),"-",ce(r0$AUC_upper,3),")");legend(if(type=="ROC")"bottomright"else"topright",labels,col=mcols,lty=c(1,2,3,1),lwd=c(1,1,1,1.8),cex=.57,bty="n")
}
# 09. Same 2 x 4 ROC style as the user's earlier original.
openpdf(9,"maximum_sample_heldout_procedure_ROC",16,9)
par(mfrow=c(2,4),oma=c(2,.4,2,.4));for(i in 1:8)curveplot("Test",top[i],lab(top[i]),LETTERS[i]);headfoot("Can earlier hospital reports identify later procedure-specific SSI signals?","Model fitted to targets in 2017-2022; tested on 18,132 reports in 2023-2025, including both ages and zero predicted counts. Procedure panels use all eligible test reports.");dev.off()

# 10. Review-budget curves and exact table.
openpdf(10,"prevention_review_capacity",14,9)
layout(matrix(c(1,2,3,3),2,2,byrow=TRUE),heights=c(3,1.5));par(oma=c(2,.4,2,.4))
for(k in 1:2){par(mar=c(4.5,4.8,2.3,1));plot(0,0,type="n",xlim=c(0,1),ylim=c(0,1),xlab="Fraction of reports selected for prevention review",ylab=if(k==1)"Fraction of future SSI signals identified"else"Signals among selected reports",main=c("A  Signals captured at each review budget","B  Review yield")[k]);for(j in 1:4){v<-cc[cc$dataset=="Test"&cc$group=="All ages and procedures"&cc$method==methods[j],];lines(v$review_fraction,if(k==1)v$alert_capture else v$precision,col=mcols[j],lwd=if(j==4)2 else 1.2,lty=c(1,2,3,1)[j])};if(k==1)abline(0,1,lty=3,col=GREY);abline(v=c(.1,.2,.3),col="#BBBBBB",lty=3);legend("bottomright",mlabs,col=mcols,lty=c(1,2,3,1),bty="n",cex=.7)}
par(mar=c(0,0,1,0));empty(c(0,1),c(0,6));text(.01,5.6,"C  Added signal capture versus prior SSI count, paired hospital bootstrap",adj=0,font=2)
hx<-c(.01,.22,.40,.63,.88);hh<-c("Review budget","Model capture, %","Prior-count capture, %","Added capture, percentage points (95% CI)","P; BH q (3 budgets)")
for(j in 1:5)text(hx[j],4.55,hh[j],adj=if(j==1)0 else .5,font=2,cex=.68)
zz<-do.call(rbind,lapply(c("capture_10","capture_20","capture_30"),function(m)paired(metric=m)));qq<-p.adjust(zz$p_centered_bootstrap,"BH")
for(i in 1:3){yy<-3.5-(i-1)*1.05;rect(0,yy-.42,1,yy+.42,col=LIGHT,border=NA);vv<-c(paste0(i*10,"%"),ce(100*zz$combined[i]),ce(100*zz$comparator_estimate[i]),sprintf("%+.2f (%.2f-%.2f)",100*zz$difference[i],100*zz$lower[i],100*zz$upper[i]),paste0(pstr(zz$p_centered_bootstrap[i]),"; ",pstr(qq[i])));for(j in 1:5)text(hx[j],yy,vv[j],adj=if(j==1)0 else .5,cex=.75)}
headfoot("How can hospitals direct limited prevention-review capacity toward future SSI signals?","18,132 held-out reports, 3,540 signals, 337 sites. Tied scores share the cutoff budget proportionally. Paired comparisons use 1,999 hospital resamples and centered-null P-values. The 10% result does not show a clear advantage over prior SSI count.");dev.off()

# 11. Calibration and precision-recall.
openpdf(11,"prediction_calibration_and_precision_recall",14,7.5)
par(mfrow=c(1,2),oma=c(2,.5,2,.5));curveplot("Test","All ages and procedures","Future SSI signal identification","A","PR")
par(mar=c(4.5,4.8,2.7,1));plot(0,0,type="n",xlim=c(0,.7),ylim=c(0,.7),xlab="Mean predicted probability of an annual SSI signal",ylab="Observed fraction of reports with an SSI signal",main="B  Does predicted probability match experience?");abline(0,1,lty=2,col=GREY)
for(i in 1:3){v<-cal[cal$dataset=="Test"&cal$group==paste("Target year",2022+i),];if(nrow(v)){segments(v$mean_prediction,v$observed_lower,v$mean_prediction,v$observed_upper,col=adjustcolor(cols[i],.45));lines(v$mean_prediction,v$observed_alert_fraction,col=cols[i],type="b",pch=i,cex=.7)}}
v<-cal[cal$dataset=="Test"&cal$group=="All ages and procedures",];if(nrow(v))lines(v$mean_prediction,v$observed_alert_fraction,col="black",type="b",pch=16,lwd=2)
legend("topleft",c("2023","2024","2025","Pooled 2023-2025"),col=c(cols[1:3],"black"),pch=c(1:3,16),lty=1,bty="n",cex=.75);j<-CJ[CJ$dataset=="Test"&CJ$group=="All ages and procedures",];cl<-CAL[CAL$dataset=="Test"&CAL$group=="All ages and procedures",];legend("bottomright",c(paste0("Joint calibration P",pstr(j$p)),paste0("Intercept: ",sprintf("%.3f (%.3f-%.3f)",cl$calibration_value[cl$term=="(Intercept)"],cl$calibration_lower[cl$term=="(Intercept)"],cl$calibration_upper[cl$term=="(Intercept)"])),paste0("Slope: ",sprintf("%.3f (%.3f-%.3f)",cl$calibration_value[cl$term=="lp"],cl$calibration_lower[cl$term=="lp"],cl$calibration_upper[cl$term=="lp"]))),bty="n",cex=.65)
headfoot("Is future-signal prediction both useful and well calibrated?","18,132 held-out reports. Calibration groups are prediction deciles. Pooled mean prediction 17.78%; observed signals 19.52%. AP = average precision.");dev.off()

# 12. Independent geographic transport, clearly historical.
openpdf(12,"geographic_transport_to_Oregon",14,8.5)
par(mfrow=c(1,2),oma=c(3,.4,2,.4));curveplot("Test","All ages and procedures","California, held-out 2023-2025","A");curveplot("Oregon external","All ages and procedures","Oregon, historical 2017 transport check","B")
headfoot("Does a California report-based signal model travel to another reporting system?","California: 18,132 reports, 3,540 signals. Oregon: 209 reports, 55 signals, 46 sites. Oregon 2017 is a historical geographic check of a model fitted through 2022.");dev.off()

# 13. Observed procedure incidence with uncertainty and expected-rate markers.
openpdf(13,"all_procedure_SSI_incidence_and_precision",14,11.5)
par(oma=c(2,.3,2,.3),mar=c(4.5,1,1,1));empty(c(0,1),c(0,30));z<-pr[order(pr$rate,decreasing=TRUE),];mx<-max(z$rate_hi,1000*z$expected/z$operations)*1.02
hx<-c(.01,.28,.38,.87,.99);hh<-c("Procedure","Operations","SSI cases","Observed /\npredicted\n(95% CI)","Annual trend\naIRR; q")
for(j in seq_along(hx))text(hx[j],29.2,hh[j],adj=if(j==1)0 else if(j==5)1 else .5,font=2,cex=.72)
for(i in 1:nrow(z)){r<-z[i,];yy<-28.6-i;if(i%%2)rect(0,yy-.4,1,yy+.4,col=LIGHT,border=NA);text(.01,yy,lab(r$name),adj=0,cex=.72);text(.28,yy,fmt(r$operations),cex=.68);text(.38,yy,fmt(r$cases),cex=.68);ci(.45+.37*r$rate/mx,.45+.37*r$rate_lo/mx,.45+.37*r$rate_hi/mx,yy);points(.45+.37*1000*r$expected/r$operations/mx,yy,pch=4,cex=.7);text(.87,yy,sprintf("%.2f (%.2f-%.2f)",r$oe,r$oe_lo,r$oe_hi),cex=.64);rr<-trend(r$name);text(.99,yy,if(nrow(rr))paste0(ce(rr$effect,3),"; ",pstr(rr$q_BH))else "NE",adj=1,cex=.58)}
ticks<-pretty(c(0,mx),5);ticks<-ticks[ticks<=mx];axis(1,.45+.37*ticks/mx,ticks,cex.axis=.75);mtext("Observed SSIs per 1,000 operations; blue points and 95% hospital-cluster intervals",1,2.4,cex=.8);rr<-GW[GW$model=="SSI_rate_age_procedure_year"&GW$term=="procedure",];mtext(paste0("Hospital-cluster adjusted procedure heterogeneity: P",pstr(rr$p)),3,line=-.2,adj=0,cex=.75);headfoot("Which procedures combine high SSI incidence, substantial burden, and precise evidence?","All 6,737,972 operations and 37,525 SSIs. Crosses = source-predicted SSI rates. Observed/predicted ratios use pooled counts, never averages of report-level ratios.");dev.off()

# 14. All procedure trajectories, with all available age-specific reports.
openpdf(14,"annual_procedure_SSI_trajectories",16,13)
par(mfrow=c(7,4),oma=c(2,.4,2,.4));for(i in 1:28){g<-aa[aa$procedure==key$procedure[i],];par(mar=c(2.4,3.1,2.0,.5),cex=.7);plot(0,0,type="n",xlim=c(2016,2025),ylim=c(0,max(g$rate)*1.08+.1),axes=FALSE,xlab="",ylab="SSIs / 1,000",main=paste(key$code[i],key$label[i]),cex.main=.91);for(j in 1:2){v<-g[g$age==c("Adult","Pediatric")[j],];if(nrow(v)){v<-merge(data.frame(year=2016:2025),v,by="year",all.x=TRUE,sort=TRUE);lines(v$year,v$rate,type="b",col=c(BLUE,ORANGE)[j],pch=c(16,1)[j],cex=.4,lwd=1)}};axis(1,c(2016,2020,2025),c("2016","2020","2025"),cex.axis=.8);axis(2,cex.axis=.8);box(bty="l");rr<-trend(key$procedure[i]);mtext(est(rr,"aIRR/year",TRUE),3,line=.05,adj=0,cex=.52)};headfoot("Are procedure-specific SSI patterns changing similarly in adults and children?","All 28 procedures, 2016-2025. Blue filled points = adult; orange open points = pediatric. Rates are observed annual summaries; absent age-procedure combinations are left unplotted.");dev.off()

# 15. Signal history: observed data and adjusted prospective-context sensitivity.
openpdf(15,"adjusted_signal_history_and_service_context",16,10)
layout(matrix(1:4,2,2,byrow=TRUE),heights=c(1,1.35));par(oma=c(2.2,.4,2,.4))
v<-hi[hi$name=="All ages",];v<-v[match(c("00","01","10","11"),v$history),];par(mar=c(4.5,5.4,2.7,1));plot(0,0,type="n",xlim=c(.5,4.5),ylim=c(0,70),xaxt="n",xlab="Two preceding annual report states",ylab="Following reports above predicted (%)",main="A  Observed following-year signal frequency");for(i in 1:4){rect(i-.28,0,i+.28,v$next_alert_pct[i],col=histcol[i],border=NA);segments(i,v$lo[i],i,v$hi[i],lwd=1.2);text(i,v$hi[i]+3,paste0(ce(v$next_alert_pct[i]),"%"),cex=.8)};axis(1,1:4,c("00","01","10","11"));mtext("46,465 reports; 00 = two quiet years; 10 = earlier signal, then quiet",1,line=3.2,cex=.65)
par(mar=c(4.5,5.4,2.7,1));plot(0,0,type="n",xlim=c(.5,4.5),ylim=c(0,.55),xaxt="n",xlab="Two preceding annual report states",ylab="Standardized following-year signal probability",main="B  Adjusted logistic sensitivity");for(i in 1:4){r<-STD[as.character(STD$history)==c("00","01","10","11")[i],];if(!nrow(r))r<-STD[STD$history==as.numeric(c("00","01","10","11")[i]),];segments(i,r$lower,i,r$upper,col=histcol[i],lwd=1.4);points(i,r$standardized_alert_probability,col=histcol[i],pch=16);text(i,r$upper+.03,ce(r$standardized_alert_probability,3),cex=.8)};axis(1,1:4,c("00","01","10","11"));mtext("Observed histories standardized for procedure, age, year and prior volume/risk",1,line=3.2,cex=.65)
v<-MEM[match(c("history10 versus history00","history01 versus history00","history11 versus history00"),MEM$comparison),];z<-data.frame(label=c("10 vs 00\nEarlier signal, then quiet","01 vs 00\nEmerging signal","11 vs 00\nTwo prior signals"),effect=v$RR,lower=v$lower,upper=v$upper,p=v$p,q=v$q_BH);foresttable(z,"C  Adjusted history associations",xlim=c(1,3))
v<-EAR[grep("10|01|11",EAR$comparison),];v<-v[match(c("10 versus 00","01 versus 00","11 versus 00"),v$comparison),];if(any(is.na(v$RR))){v<-EAR[1:3,]};z<-data.frame(label=v$comparison,effect=v$RR,lower=v$lower,upper=v$upper,p=v$p);foresttable(z,"D  Earlier service context, separate baseline",xlim=c(1,3));mtext("Baseline 2016-2019; targets 2022-2025; 19,978 reports",1,line=3.5,cex=.65)
headfoot("Does prior SSI history retain information after adjustment for service context?","Hospital-cluster robust inference. C: modified-Poisson adjusted RRs. D: logistic standardized RRs with a disjoint earlier-service baseline. P-values describe forward associations.");dev.off()

# 16. Choosing the objective: future SSI case burden versus binary report alerts.
openpdf(16,"future_SSI_case_capture_tradeoff",14,8.5)
layout(matrix(c(1,2),1,2),widths=c(1.1,1));par(oma=c(2.3,.5,2,.5))
zz<-CASE[CASE$comparator=="prior_cases",];par(mar=c(4.8,5.2,2.8,1));plot(zz$capacity*100,zz$combined_capture*100,type="b",pch=16,col="black",lwd=2,xlim=c(8,32),ylim=c(0,100),xlab="Reports selected for prevention review (%)",ylab="Following-year SSI cases in selected reports (%)",main="A  Which rule captures more future SSI cases?");lines(zz$capacity*100,zz$comparator_capture*100,type="b",pch=17,col=ORANGE,lwd=1.4);legend("topleft",c("Combined signal model","Prior SSI count"),col=c("black",ORANGE),pch=c(16,17),lty=1,bty="n",cex=.8)
par(mar=c(1,1,2,1));empty(c(0,1),c(0,7));text(0,6.6,"B  Paired future-case capture comparison",adj=0,font=2);text(.02,5.7,"Review budget",adj=0,font=2,cex=.8);text(.53,5.7,"Added case capture, pp (95% CI)",font=2,cex=.75);text(.99,5.7,"P",adj=1,font=2)
for(i in 1:3){yy<-4.8-(i-1)*1.1;rect(0,yy-.4,1,yy+.4,col=LIGHT,border=NA);text(.02,yy,paste0(zz$capacity[i]*100,"%"),adj=0);text(.53,yy,sprintf("%+.2f (%.2f-%.2f)",100*zz$difference[i],100*zz$lower[i],100*zz$upper[i]),cex=.78);text(.99,yy,pstr(zz$p[i]),adj=1,cex=.78)}
text(0,.65,"Match the ranking rule to the review objective.\nFuture report signals and future SSI case burden\nare distinct operational targets.",adj=0,cex=.85)
headfoot("Does a model that identifies future SSI signals also capture the most future SSI cases?","18,132 held-out reports and 11,897 observed following-year SSIs. Frozen model and prior-count rule compared using 1,999 paired hospital resamples; ties share budget proportionally.");dev.off()

# 17. Concordance of changes in incidence and observed/predicted burden.
ch<-read.csv(file.path(T,"early_late_procedure_change.csv"));ch<-merge(ch,key,by="procedure",sort=FALSE)
openpdf(17,"procedure_change_concordance_map",15,10)
layout(matrix(c(1,2),1,2),widths=c(1.5,1));par(oma=c(2,.4,2,.4));par(mar=c(4.7,5,2.5,1));mx<-max(abs(c(ch$rate_log2_change,ch$oe_log2_change)))*1.15
plot(0,0,type="n",xlim=c(-mx,mx),ylim=c(-mx,mx),xlab="Change in observed SSI rate (log2 late / early)",ylab="Change in observed / predicted burden (log2 late / early)",main="A  Incidence and benchmark changes");rect(-mx,0,0,mx,col="#FAE7EA",border=NA);rect(0,-mx,mx,0,col="#FAE7EA",border=NA);rect(-mx,-mx,0,0,col="#E6F1EC",border=NA);rect(0,0,mx,mx,col="#E6F1EC",border=NA);abline(h=0,v=0,lty=2,col=GREY);fc<-setNames(c(BLUE,GREEN,ORANGE,PURPLE),sort(unique(ch$family)));points(ch$rate_log2_change,ch$oe_log2_change,pch=21,bg=fc[ch$family],col="white",cex=.7+2*sqrt(ch$late_operations/max(ch$late_operations)));tx<-ch$rate_log2_change;ty<-ch$oe_log2_change+.055;for(iter in 1:250){for(a in 1:(length(tx)-1))for(b in (a+1):length(tx)){if(abs(tx[a]-tx[b])<.095&&abs(ty[a]-ty[b])<.072){direction<-if(ty[a]>=ty[b])1 else -1;ty[a]<-ty[a]+.009*direction;ty[b]<-ty[b]-.009*direction}};ty<-pmax(-mx+.04,pmin(mx-.04,ty))};segments(ch$rate_log2_change,ch$oe_log2_change,tx,ty,col="#888888",lwd=.4);text(tx,ty,ch$code,cex=.59);legend("topleft",names(fc),col=fc,pch=16,bty="n",cex=.63)
par(mar=c(0,0,2,0));empty(c(0,1),c(-.8,30));text(0,29.5,"B  Adjusted late / early incidence comparisons",adj=0,font=2,cex=.9);text(.72,28.4,"Late / early aIRR (95% CI)",cex=.7,font=2);text(.98,28.4,"BH q",cex=.7,font=2)
for(i in 1:28){r<-ch[match(key$code[i],ch$code),];yy<-28-i;if(i%%2)rect(0,yy-.4,1,yy+.4,col=LIGHT,border=NA);text(0,yy,paste(r$code,r$label),adj=0,cex=.65);rr<-EL[EL$procedure==r$procedure,];text(.72,yy,if(nrow(rr))sprintf("%.2f (%.2f-%.2f)",rr$effect,rr$lower,rr$upper)else "NE",cex=.60);text(.98,yy,if(nrow(rr))pstr(rr$q_BH)else "NE",cex=.60)}
headfoot("Which procedures show aligned or conflicting changes in observed incidence and benchmark burden?","Early = 2016-2019; late = 2022-2025, all reports in those windows. Bubble area reflects late operations. Map uses half-count smoothing and is descriptive. Table: age-adjusted count models, operation offsets, hospital-cluster CIs; BH q across 28 tests.");dev.off()

# 18. Translational evidence map, explicit proposed review actions.
openpdf(18,"evidence_to_prevention_review_map",16,12)
layout(matrix(c(1,2),2),heights=c(4,1.25));par(oma=c(2,.3,2,.3));par(mar=c(1,0,3,0));empty(c(0,1),c(0,31));r<-pr[order(pr$cases,decreasing=TRUE),]
heads<-c("Procedure","SSI cases","SSI / 1,000","O / predicted","Next-year signal aRR\n(95% CI)","BH q","National SSI\nmicrobiology category")
xs<-c(.01,.29,.40,.52,.65,.79,.93);for(j in 1:7)text(xs[j],30,heads[j],adj=if(j==1)0 else .5,font=2,cex=.7)
for(i in 1:nrow(r)){yy<-29-i;if(i%%2)rect(0,yy-.4,1,yy+.4,col=LIGHT,border=NA);text(.01,yy,lab(r$name[i]),adj=0,cex=.70);text(.29,yy,fmt(r$cases[i]),cex=.7);text(.40,yy,ce(r$rate[i]),cex=.7);text(.52,yy,ce(r$oe[i],2),cex=.7);rr<-procRR(r$name[i]);text(.65,yy,if(nrow(rr))sprintf("%.2f (%.2f-%.2f)",rr$effect,rr$lower,rr$upper)else "NE",cex=.65);text(.79,yy,if(nrow(rr))pstr(rr$q_BH)else "NE",cex=.7);cx<-XD[XD$california_procedure==r$name[i],];text(.93,yy,cx$national_body_site_category,cex=.7)}
par(mar=c(0,.5,0,.5));empty(c(0,1),c(0,1));boxx<-c(0,.34,.68);ttl<-c("Recurring signals: structured service review","New signals: focused case and process review","Stewardship: connect the signal to local evidence")
txt<-c("Prioritize services with repeated above-predicted reports.\nReview SSI surveillance, case mix and prevention processes.\nTrack the next annual report using the same definitions.","Review the cases behind a new above-predicted report.\nCheck prophylaxis timing, dosing and redosing,\nskin preparation and procedure-specific prevention.","Audit prophylaxis selection and duration against guidelines.\nRequest local procedure-linked cultures and susceptibility.\nUse those findings to consider any regimen change.")
for(j in 1:3){rect(boxx[j],.08,boxx[j]+.31,.98,col=LIGHT,border=NA);text(boxx[j]+.01,.87,ttl[j],adj=0,font=2,cex=.78);text(boxx[j]+.01,.52,txt[j],adj=0,cex=.76)}
headfoot("How can report-derived SSI signals guide prevention and antimicrobial stewardship review?","All 28 procedures. Forward aRR uses hospital-cluster inference with 28-test BH correction. National microbiology categories provide separate contextual evidence, not California isolate linkage. Proposed review pathways are supported by SSI-prevention guidance and the separate pathogen/AMR analyses in Figures 21-26.");dev.off()
write.csv(do.call(rbind,kmres),file.path(T,"survival_summary_statistics.csv"),row.names=FALSE)
writeLines(capture.output(sessionInfo()),file.path(B,"reproducibility/R_session_information.txt"))
