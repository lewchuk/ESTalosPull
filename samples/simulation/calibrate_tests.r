source("../../rscript/talos_lib.r")
source("../../rscript/plot_talos_data.r")
library("gridExtra")
library("boot")

calibration = read.csv("calibration_simulation_detect.csv")

pdf(file="calibration_results.pdf")

calibration.sample = ddply(calibration, .(test_name,sample_size), function(f) data.frame(mean=mean(f$less_ratio), ci=norm.ci(t0=mean(f$less_ratio), t=f$less_ratio)))

plot_detection_curve = function(f) {
  plot = ggplot(data = f, mapping=aes(x=sample_size)) + geom_line(aes(y=mean))
  plot = plot + geom_line(aes(y=ci.V2), colour="red") + geom_line(aes(y=ci.V3), colour="red")
  plot = plot + geom_abline(intercept=0.95, slope=0, colour="blue")
  plot = plot + scale_y_continuous(formatter="percent", limits=c(0,1))
  plot = plot + opts(title=paste("Detection Curves: ", f$test_name[1]))
  plot
}

p = daply(calibration.sample, .(test_name), plot_detection_curve)
print(p)

find_range = function(f) {
  mean = min(f[which(f$mean > 0.95),'sample_size']) + 1
  min = min(f[which(f$ci.V2 > 0.95), 'sample_size']) + 1
  max = min(f[which(f$ci.V3 > 0.95), 'sample_size']) + 1
  data.frame(lower = max, mean=mean, upper=min)
}

calib.out = ddply(calibration.sample, .(test_name), find_range)

print(calib.out)


dev.off()

