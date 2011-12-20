source("../../rscript/talos_lib.r")
pine = load_data("pine","runs")
pine.fedora = subset(pine, os == "fedora" & !(starttime==1322991336 & test_name=="replaceimages.html"))

write_data_set = function(frame) {
  test_name = frame$test_name[1];
  write(subset(frame, run_num != 0)$value, file=paste("samples/", test_name, ".dat", sep=""), sep="\n")
}

d_ply(pine.fedora, .(test_name), write_data_set)
