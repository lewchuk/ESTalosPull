library("ggplot2")

# Given continuous data determine where ticks should go
determine_tick_positions <- function(data_list, num_ticks=14) {
  r=range(data_list)
  period = round_any((r[2]-r[1])/num_ticks, 1, ceiling)
  c(1:num_ticks) * period + r[1]
}

# Given time data determine the spacing between ticks in number of days
determine_tick_size <- function(data, num_ticks=14) {
  dates = range(data$starttime)
  min = round_any(dates[1]/86400, 1, floor)
  max = round_any(dates[2]/86400, 1, ceiling)
  period = round_any((max-min)/num_ticks, 1, ceiling)
  paste(period, "days")
}

###### TestSuite level plots ######

# Replicate graph serve output for builds of a particular os
plot_graph_serve <- function(build_data) {
  os_name = unique(build_data$os)[1]
  testsuite = unique(build_data$testsuite)[1]
  build_data$machine <- factor(build_data$machine)
  plot <- ggplot(data = build_data, aes(x=date))
  plot <- plot + scale_x_datetime(name="Date", format="%b/%d", major=determine_tick_size(build_data))
  plot <- plot + opts(legend.position = "none")
  plot <- plot + geom_line(aes(y=new_result, colour=machine))
  plot <- plot + opts(title=paste("Graph Serve output for", testsuite, "on", os_name))
  plot
}

# Plot the test suite result over time
plot_build_over_time <- function(build_data) {
  os_name = unique(build_data$os)[1]
  testsuite = unique(build_data$testsuite)[1]
  plot <- ggplot(data = build_data, aes(x=date))
  plot <- plot + scale_x_datetime(name="Date", format="%b/%d", major=determine_tick_size(build_data))
  plot <- plot + geom_line(aes(y=new_result))
  plot <- plot + opts(title=paste("Average output for", testsuite, "on", os_name))
  plot
}

###### Component Level Plots ######

# Plot the median of a component over time
# If breaks is not NULL, add vertical lines for breaks
plot_medians_with_breaks <- function(component_data, breaks) {
  os_name = as.character(unique(component_data$os)[1])
  test = as.character(unique(component_data$short_uri)[1])
  plot = ggplot(component_data, aes(x=date))
  plot = plot + geom_line(aes(y=new_median))
  plot = plot + opts(title=paste("Component medians", os_name, test))
  plot = plot + scale_x_datetime(name="Date", format="%b/%d", major=determine_tick_size(component_data))
  if (!is.null(breaks)) {
    breaks = subset(breaks, os == os_name & short_uri == test)
    if (dim(breaks)[1] > 0) {
        plot <- plot + geom_vline(xintercept=breaks$dates)
    }
  }
  plot
}

# Plot the median of a component over time
plot_medians_by_time <- function(component_data) {
  plot_medians_with_breaks(component_data, NULL)
}

# Given data for a single operating system, plot the medians of each component with different colours.
plot_stacked_medians <- function(component_data) {
  os_name = unique(component_data$os)[1]
  plot = ggplot(component_data, aes(x=date))
  plot = plot + geom_line(aes(y=new_median, colour=short_uri))
  plot = plot + scale_colour_discrete(name="Page name")
  plot = plot + opts(title=paste("Component medians", os_name))
  plot = plot + scale_x_datetime(name="Date", format="%b/%d", major=determine_tick_size(component_data, 7))
  plot
}

###### Run Level Plots ######

# Plot superimposed test runs
plot_stacked_runs <- function(run_data, with_transparency=FALSE) {
  test = unique(run_data$test_name)[1]
  os_name = unique(run_data$os)[1]
  p <- ggplot(data=run_data, aes(x=factor(run_num), y=value, group=index))
  if (with_transparency) {
    p <- p + geom_line(colour = alpha("black", 1/5))
  } else {
    p <- p + geom_line()
  }
  p <- p + opts(title=paste(test, os_name, sep=" : "))
  p <- p + scale_x_discrete(name="Run index") + scale_y_continuous(name="Test Result (ms)")
  p
}

# Plot superimposed test runs along with a red line plotting the average at each run index
plot_stacked_runs_with_mean <- function(run_data, run_means,  with_transparency=FALSE) {
  plot = plot_stacked_runs(run_data, with_transparency)
  test_means = subset(run_means, test_name == run_data$test_name[1])
  plot = plot + geom_line(data=test_means, aes(x=factor(run_num), y=mean, group="none"), colour="red")
  plot
}

# Plot the histogram of run values
plot_run_histogram <- function(run_data, trim_size=1, bin_breaks=60) {
    run_data_trim = run_data[order(run_data$value)[0:(trim_size*dim(run_data)[1])],]
    ra = range(run_data_trim$value)
    bw = max(1, (ra[2] - ra[1]) / bin_breaks)
    test = unique(run_data$test_name)[1]
    os_name = unique(run_data$os)[1]
    plot <- ggplot(data = run_data_trim, aes(x=value))
    plot <- plot + geom_histogram(aes(y = ..count..), binwidth=bw)
    plot <- plot + opts(title=paste("Run Histogram for", test, "on", os_name))
    plot
}

###### SIMULATION PLOTS ######

# Plot the confidence curves for a particular test
plot_confidence_curves <- function(confidence_frame) {
  plot <- ggplot(data=confidence_frame, aes(x=sample_size))
  plot <- plot + geom_line(aes(y=more_ratio), colour="blue") + geom_line(aes(y=less_ratio), colour="red")
  plot = plot + opts(title=paste("1% Change Confidence Curves:", confidence_frame$test_name[1], confidence_frame$os[1]))
  plot = plot + scale_y_continuous(name="Detection Chance", formatter="percent", limits=c(0,1))
  plot
}

# Plot the histograms of means at different sample sizes
plot_sample_size_histograms <- function(confidence_frame, pop_frame) {
  r = range(confidence_frame$mean)
  test_name = confidence_frame$test_name[1]
  sample_sizes = data.frame(test_name = test_name, sample_size = unique(confidence_frame$sample_size))
  mean_array = merge(sample_sizes, pop_frame)
  plot = ggplot(data=confidence_frame, aes(x=mean, y=..count..)) + geom_bar(binwidth=max((r[2]-r[1])/30,1))
  plot = plot + geom_vline(data = mean_array, aes(xintercept=model_less), colour="red")
  plot = plot + geom_vline(data = mean_array, aes(xintercept=model_more), colour="blue")
  plot = plot + opts(title=paste("Sample Mean Histograms:", test_name, confidence_frame$os[1]))
  plot = plot + facet_wrap( ~ sample_size)
  plot = plot + scale_x_continuous(breaks=determine_tick_positions(confidence_frame$mean, 3))
  plot
}

# For a single sample size plot the confidence versus variance
plot_single_confidence_sd_scatter <- function(sample_pop_frame) {
  os = sample_pop_frame$test_name[1]
  sample_pop_frame$test_name=factor(sample_pop_frame$test_name, levels=sample_pop_frame$test_name[rev(order(sample_pop_frame$less_ratio))])
  plot = ggplot(data=sample_pop_frame, aes(x = (sd/mean), y = less_ratio, colour=test_name))
  plot + geom_point() + opts(title = paste("Sample Size:", sample_pop_frame$sample_size[1], os))
}


