source("../rscript/talos_lib.r")
source("../rscript/plot_talos_data.r")
tsvg = load_data("tsvg_sample", "runs")
tdhtml = load_data("tdhtml_sample", "runs")

pdf(file="non_normal.pdf")

plot_run_histogram(subset(tsvg, test_name=="hixie-002.xml" & os == "fedora" & run_num!=0), trim=0.99, bin_size=1)
plot_run_histogram(subset(tsvg, test_name=="hixie-005.xml" & os == "lion" & run_num!=0), trim=0.99, bin_size=1)
plot_run_histogram(subset(tdhtml, test_name=="imageslide.html" & os == "fedora" & run_num!=0), trim=0.99, bin_size=1)
plot_run_histogram(subset(tdhtml, test_name=="layers6.html" & os == "fedora" & run_num!=0), trim=0.99, bin_size=1)
plot_run_histogram(subset(tdhtml, test_name=="scrolling.html" & os == "win7"& run_num!=0), trim=0.99, bin_size=1)
plot_run_histogram(subset(tdhtml, test_name=="fadespacing.html" & os == "xp"& run_num!=0), trim=0.99, bin_size=1)

dev.off()
