source("../rscript/talos_lib.r")
source("../rscript/plot_talos_data.r")
tsvg = load_data("tsvg_sample", "runs")
tdhtml = load_data("tdhtml_sample", "runs")

pdf(file="first_run.pdf")

plot_run_histogram(subset(tsvg, test_name=="composite-scale.svg" & os == "fedora"), trim=0.99) + facet_grid(. ~ run_num)
plot_run_histogram(subset(tsvg, test_name=="gearflowers.svg" & os == "fedora"), trim=0.99) + facet_grid(. ~ run_num)
plot_run_histogram(subset(tdhtml, test_name=="imageslide.html" & os == "fedora"), trim=0.99) + facet_grid(. ~ run_num)
plot_run_histogram(subset(tdhtml, test_name=="fadespacing.html" & os == "fedora64"), trim=0.99) + facet_grid(. ~ run_num)
plot_run_histogram(subset(tdhtml, test_name=="scrolling.html" & os == "snowleopard"), trim=0.99) + facet_grid(. ~ run_num)
plot_run_histogram(subset(tdhtml, test_name=="colorfade.html" & os == "snowleopard"), trim=0.99) + facet_grid(. ~ run_num)
plot_run_histogram(subset(tdhtml, test_name=="mozilla.html" & os == "win7"), trim=0.99) + facet_grid(. ~ run_num)

dev.off()
