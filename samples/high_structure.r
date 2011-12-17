source("../rscript/talos_lib.r")
source("../rscript/plot_talos_data.r")
pine = load_data("pine", "runs")

pdf(file="high_structure.pdf")

pine = subset(pine, !(starttime==1322991336 & test_name=="replaceimages.html"))
pine.population = ddply(pine, .(os, test_name, run_num), function(f) data.frame(mean=mean(f$value)))

plots.fed = daply(subset(pine, os =="fedora"), .(test_name), plot_stacked_runs_with_mean, run_means=subset(pine.population, os == "fedora"))
plots.fed[['colorfade.html']] + scale_x_discrete(breaks=seq(0,100,5), name="Run Index")
plots.fed[['replaceimages.html']] + scale_x_discrete(breaks=seq(0,100,5), name="Run Index")

plots.xp = daply(subset(pine, os =="xp"), .(test_name), plot_stacked_runs_with_mean, run_means=subset(pine.population, os == "xp"))

plots.xp[['colorfade.html']] + scale_x_discrete(breaks=seq(0,100,5), name="Run Index")
plots.xp[['mozilla.html']] + scale_x_discrete(breaks=seq(0,100,5), name="Run Index")
plots.xp[['slidein.html']] + scale_x_discrete(breaks=seq(0,100,5), name="Run Index")
dev.off()
