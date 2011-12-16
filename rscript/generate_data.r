source("changepoint.r")
library("plyr")
source("talos_lib.r")

###### CHANGE POINT ANALYSIS ######

# Generate breakpoints based on the new median
# Returns a frame of builds that are the last of a regime
generate_break_data_single <- function(component_data) {
    cp_r = find_multiple_changepoints(component_data$new_median)
    if (is.null(cp_r)) {
      return(NULL)
    }
    data.frame(component_data[(cp_r$pos-1),], cp_r)
}

# Given component data across multiple tests and operating systems
# Runs the breakpoint analysis on all os, component pairs
generate_break_data <- function(component_data) {
 breaks = ddply(component_data, .(os, test_name), generate_break_data_single)
 breaks[,c('revision', 'machine', 'starttime', 'testgroup', 'testsuite', 'os', 'buildtype', 'tree', 'test_name', 'mag', 'conf')]
}

###### LINEAR MODELS ######

generate_run_only_model <- function(run_data) {
  run_1_mean = mean(subset(run_data, run_num==1)$value)
  scaled = run_data$value - run_1_mean
  data = transform(run_data, scaled=scaled)
  linear = lm(data=data, formula = scaled ~ factor(run_num) - 1)
  list(lm = linear, center=run_1_mean)
}

generate_run_model <- function(run_data) {
  data = subset(run_data, run_num != 0)
  scaled = scale(data$value)
  data = transform(data, scaled = scaled)
  linear = lm(data=data, formula = scaled ~ machine - 1)
  list(lm = linear, center = attr(scaled, 'scaled:center'), scale = attr(scaled, 'scaled:scale'))
}

generate_run_id_model <- function(run_data) {
  data = subset(run_data, run_num != 0)
  breaks = length(unique(data$id))
  if (breaks < 2) {
    return(generate_run_model(run_data))
  }
  scaled = scale(data$value)
  data = transform(data, scaled = scaled)
  linear = lm(data=data, formula = scaled ~ machine + id - 1)
  list(lm = linear, center = attr(scaled, 'scaled:center'), scale = attr(scaled, 'scaled:scale'))
}

generate_new_median_model <- function(comp_data) {
  scaled = scale(comp_data$new_median)
  data = transform(comp_data, scaled = scaled)
  linear = lm(data=data, formula = scaled ~ machine -1)
  list(lm = linear, center = attr(scaled, 'scaled:center'), scale = attr(scaled, 'scaled:scale'))
}

generate_new_mean_model <- function(comp_data) {
  scaled = scale(comp_data$new_average)
  data = transform(comp_data, scaled = scaled)
  linear = lm(data=data, formula = scaled ~ machine -1)
  list(lm = linear, center = attr(scaled, 'scaled:center'), scale = attr(scaled, 'scaled:scale'))
}

generate_combined_model <- function(comp_data) {
  scaled = scale(comp_data$new_median)
  data = transform(comp_data, scaled = scaled)
  linear = lm(data=data, formula = scaled ~ machine + test_name - 1)
  list(lm = linear, center = attr(scaled, 'scaled:center'), scale = attr(scaled, 'scaled:scale'))
}

# Generates a model based on either run or component data using
# the generate_*_model function given in .func
generate_model_single <- function(data, .func, ...) {
  test_name <- unique(data$short_uri)[1]
  os_name <- unique(data$os)[1]

  mod = .func(data, ...)

  anova <- aov(mod$lm)
  model <- list(test_name = as.character(test_name), os_name = as.character(os_name), lm = mod$lm, aov = anova, center = mod$center, scale = mod$scale)
  model
}

# Converts statistical significance to levels, the levels are signed to indicate the sign of the effect
convert_sig_to_level <- function(sig, effect, ...) {
    level = 0
    if (sig < 0.001) level = 4
    else if (sig < 0.01) level = 3
    else if (sig < 0.05) level = 2
    else if (sig < 0.1) level = 1

    level * sign(effect)
}

# Extracts information about machine effects from a linear model
model_frame <- function(m) {
  coeff_m = summary(m$lm)$coefficients
  pos = grepl("^machine.*", row.names(coeff_m))
  effects = coeff_m[pos, c(1,4)]
  dimnames(effects)[[2]] = c("effect", "sig")

  short_names = laply(row.names(effects), shorten_machine_name)
  estimate = aaply(effects[,1], round_any, accuracy=0.5)
  sig = maply(effects, convert_sig_to_level, .expand=FALSE)

  data.frame(machine=short_names, estimate=effects[,1], rounded_estimate=estimate, sig=sig, test_name=m$test_name)
}

# Count the number of instances of a test running on a machine
count_machine_test_instances <- function(data) {
  count = dim(unique(data$revision, data$starttime))[1]
  data.frame(machine=shorten_machine_name(unique(as.character(data$machine))), count)
}

# Summarize across tests the effect of machines
summarize_machines <- function(machine_frame) {
  machine = unique(as.character(machine_frame$machine))
  average_estimate = mean(machine_frame$estimate)
  total_sig = sum(machine_frame$sig)
  data.frame(machine=machine, average_estimate=average_estimate, total_sig=total_sig)
}

# given data for a single os and a model function, generate models for each test
generate_os_model <- function(data, .func, ...) {
  models = dlply(data, .(test_name), generate_model_single, .func=.func, ...)
  frame = ldply(models, model_frame)
  frame$machine = factor(frame$machine)

  machine_details = ddply(data, .(machine), count_machine_test_instances)
  model_details = ddply(frame, .(machine), summarize_machines)
  test_details = ldply(models, function(m) data.frame(test_name=m$test_name, center=m$center, scale=m$scale))
  list(model_data = frame, models=models, test_details=test_details, machine_details=merge(machine_details, model_details), os_name=models[[1]]$os_name)
}

# generate models for multiple operating systems
generate_os_models <- function(data, .func, ...) {
  dlply(data, .(os), generate_os_model, .func=.func, ...)
}
