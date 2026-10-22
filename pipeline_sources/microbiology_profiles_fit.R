O <- 'work/ssi_figure17_redesign/fourpanel_analysis'
meta <- read.csv(file.path(O,'profile_metadata.csv'),check.names=FALSE,stringsAsFactors=FALSE)
w <- read.csv(file.path(O,'profile_counts_wide.csv'),check.names=FALSE,stringsAsFactors=FALSE)
w <- w[match(meta$profile_id,w$profile_id),]
X <- as.matrix(w[,-1]);rownames(X)<-meta$profile_id
train <- meta$role=='Discovery'
clr <- function(mat,pc=.5) {z<-log(mat+pc);z-rowMeans(z)}
C<-clr(X);T<-C[train,,drop=FALSE]
# Source profiles each contribute once to learning; source volumes are composition denominators, not learning row weights.
pca<-prcomp(T,center=TRUE,scale.=FALSE)
coords<-predict(pca,C)
avsil<-function(z,lab) {
 D<-as.matrix(dist(z));ss<-numeric(length(lab))
 for(i in seq_along(lab)){
  own<-which(lab==lab[i]);own<-setdiff(own,i)
  if(!length(own)){ss[i]<-0;next}
  aa<-mean(D[i,own]);bb<-min(vapply(setdiff(unique(lab),lab[i]),function(g)mean(D[i,lab==g]),numeric(1)))
  ss[i]<-(bb-aa)/max(aa,bb)
 }
 mean(ss)
}
set.seed(20261020)
choices<-lapply(2:4,function(k){fit<-kmeans(T,centers=k,nstart=1000,iter.max=200);data.frame(k=k,tot_withinss=fit$tot.withinss,between_ratio=fit$betweenss/fit$totss,mean_silhouette=avsil(T,fit$cluster),minimum_group_size=min(table(fit$cluster)))})
write.csv(do.call(rbind,choices),file.path(O,'cluster_number_diagnostics.csv'),row.names=FALSE)
set.seed(20261020);fit<-kmeans(T,centers=3,nstart=1000,iter.max=200)
# Order clusters for stable IDs by training E.coli share. Labels remain descriptive, not mechanistic diagnoses.
rawprop<-X/rowSums(X)
clmean<-aggregate(rawprop[train,,drop=FALSE],list(cluster=fit$cluster),mean)
orderc<-order(clmean$`Escherichia coli`,decreasing=TRUE);old<-clmean$cluster[orderc];centers<-fit$centers[as.character(old),,drop=FALSE]
assign<-function(z,cen) apply(z,1,function(x)which.min(rowSums((cen-matrix(x,nrow(cen),ncol(cen),byrow=TRUE))^2)))
cl<-assign(C,centers);meta$ecotype<-cl;meta$PC1<-coords[,1];meta$PC2<-coords[,2]
write.csv(meta,file.path(O,'profile_ecotypes_and_projection.csv'),row.names=FALSE)
write.csv(data.frame(component=colnames(C),pca$rotation[,1:2]),file.path(O,'pca_component_loadings.csv'),row.names=FALSE)
write.csv(data.frame(component=paste0('PC',seq_along(pca$sdev)),variance_fraction=pca$sdev^2/sum(pca$sdev^2)),file.path(O,'pca_explained_variance.csv'),row.names=FALSE)
write.csv(data.frame(ecotype=seq_len(nrow(centers)),centers,check.names=FALSE),file.path(O,'frozen_clr_cluster_centroids.csv'),row.names=FALSE)
write.csv(data.frame(profile_id=rownames(T),training_ecotype=fit$cluster,ordered_ecotype=cl[train],rawprop[train,,drop=FALSE],check.names=FALSE),file.path(O,'training_profile_component_shares.csv'),row.names=FALSE)
# Sensitivity to pseudocount choice, relabel by nearest original centroids.
sens<-list()
for(pc in c(.25,.5,1)){
 cc<-clr(X,pc);set.seed(20261020);ff<-kmeans(cc[train,,drop=FALSE],3,nstart=1000,iter.max=200)
 map<-assign(ff$centers,centers);lab<-map[assign(cc,ff$centers)]
 sens[[as.character(pc)]]<-data.frame(profile_id=meta$profile_id,pseudocount=pc,ecotype=lab,agrees_primary=lab==cl)
}
write.csv(do.call(rbind,sens),file.path(O,'pseudocount_sensitivity.csv'),row.names=FALSE)
print(read.csv(file.path(O,'cluster_number_diagnostics.csv')))
print(meta[,c('profile_id','role','n_pathogen_reports','ecotype','PC1','PC2')],row.names=FALSE)
print(aggregate(rawprop[train,,drop=FALSE],list(ecotype=cl[train]),mean))
