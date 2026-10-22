p <- 'work/ssi_inferential_microbiology'
files <- c('category_enrichment_tests.csv','pooled_category_enrichment_tests.csv','adult_pediatric_pathogen_tests.csv','period_shift_tests.csv','depth_pathogen_tests.csv','depth_age_tests.csv','depth_period_tests.csv')
for (fn in files) {
 d <- read.csv(file.path(p,fn),check.names=FALSE)
 ps <- vapply(seq_len(nrow(d)), function(i) {
   m <- matrix(c(d$count1[i],d$total1[i]-d$count1[i],d$count0[i],d$total0[i]-d$count0[i]),nrow=2,byrow=TRUE)
   fisher.test(m)$p.value
 },numeric(1))
 d$p_underflow <- ps==0
 d$p_value <- pmax(ps,1e-300)
 d$q_value <- p.adjust(d$p_value,method='BH')
 d$p_label <- ifelse(d$p_value<.001,'P<0.001',sprintf('P=%.3f',d$p_value))
 d$q_label <- ifelse(d$q_value<.001,'q<0.001',sprintf('q=%.3f',d$q_value))
 write.csv(d,file.path(p,fn),row.names=FALSE,na='')
 cat(fn,nrow(d),'rows\n')
}
d <- read.csv(file.path(p,'global_composition_tests.csv'),check.names=FALSE)
d$p_value <- pmax(pchisq(d$chi_square,d$degrees_freedom,lower.tail=FALSE),1e-300)
d$p_label <- ifelse(d$p_value<.001,'P<0.001',sprintf('P=%.3f',d$p_value))
d$q_value <- p.adjust(d$p_value,method='BH')
write.csv(d,file.path(p,'global_composition_tests.csv'),row.names=FALSE)
