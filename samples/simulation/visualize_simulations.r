source("../../rscript/talos_lib.r")
source("../../rscript/plot_talos_data.r")
library("gridExtra")

sim_ratios = read.csv("single_run_simulation_detect.csv")
pine = load_data("../pine", "runs")
pine.fed = subset(pine, os == "fedora")

pdf(file="simulation_results.pdf")

classification = data.frame( test_name = sort(unique(pine$test_name)), id = c(2, 1, 2, 3, 3, 1, 1,1,3, 2,2,1,2,3,1,3,2,2))
classes = data.frame(id = c(1,2,3), class = factor(c('tight normal', 'wide/near normal', 'non normal'), levels=c('tight normal', 'wide/near normal', 'non normal')))

classification = merge(classification, classes)
pine.fed = merge(pine.fed, classification)
sim_ratios = merge(sim_ratios, classification)

plot_curves_by_class <- function(frame) {
  class_name = frame$class[1]
  plot = plot_confidence_curves(frame)
  plot = plot + opts(title=paste("1% Confidence Curves:", class_name))
  plot = plot + facet_grid(. ~ test_name)
  plot
}

curves = daply(sim_ratios, .(class), plot_curves_by_class)
grid.arrange(curves[[1]], curves[[2]], curves[[3]])

summarize_population = function(f) {
  mean = mean(f$value)
  lower = min(mean -1, mean * 0.99)
  higher = max(mean +1, mean * 1.01)
  c(mean = mean, lower=lower, higher=higher)
}

pine.population = ddply(pine.fed, .(test_name), summarize_population)
pine.population = merge(pine.population, classification)

plot_population_histograms_by_class = function(run_data, population_frame) {
  class_name = run_data$class[1]
  pop_frame = subset(population_frame, class==class_name)
  plot = plot_run_histogram(run_data, 0.99, bin_size=1)
  plot = plot + opts(title=paste("Run Histograms for:", class_name))
  plot = plot + facet_grid(. ~ test_name, scales="free")
  plot = plot + geom_vline(data = pop_frame, aes(xintercept=lower), colour="red")
  plot = plot + geom_vline(data = pop_frame, aes(xintercept=higher), colour="blue")
  plot
}

hists = daply(pine.fed, .(class), plot_population_histograms_by_class, population_frame = pine.population)

grid.arrange(hists[[1]], hists[[2]], hists[[3]])

dev.off()

