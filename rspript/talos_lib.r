require("plyr")

# Functions to manipulate data frames
shorten_pagename_int <- function(name, max = NULL) {
  name <- gsub(pattern="/.*/", replacement="/.../", x=name)
  if (!is.null(max)) {
    if (nchar(name) > max) {
      name = substr(name, 1, max)
    }
  }
  name
}

shorten_pagename <- function(row, index='test_name', max = 35) {
  shorten_pagename_int(row[index], max)
}

add_date_to_frame <- function(data) {
 transform(data, date=as.POSIXct(as.POSIXlt(data$starttime, origin="1970-01-01", tz="American/Los Angeles")))
}

add_short_uri <- function(data, ...) {
 transform(data, short_uri = apply(data, 1, shorten_pagename, ...))
}

fill_id <- function(frame) {
  id = 0
  for (i in 1:dim(frame)[1]) {
    if (is.na(frame[i, 'id'])) {
      frame[i, 'id'] = id
    } else {
      id = frame[i, 'id']
    }
  }
  frame
}

shorten_machine_name <- function(machine) {
  vect = strsplit(machine,"-")[[1]]
  paste(vect[(length(vect)-1):length(vect)], collapse="-")
}

# Load a csv and add additional information
load_data <- function(source, suffix, shorten_uri=TRUE,sort_data=FALSE) {
  data <- read.csv(file=paste(source, "_", suffix, ".csv", sep=""))
  if ('date' %in% names(data) {
    data <- add_date_to_frame(data)
  }
  if (shorten_uri) {
    data <- add_short_uri(data)
  }
  if (sort_data) {
    data <- data[order(data$starttime),]
  }
  data
}

# Adds an id column based on break point detection output
combine_data_with_breaks <- function(data, breaks) {
    breaks = transform(breaks, id=1:dim(breaks)[1])
    data = merge(data, breaks, by=intersect(names(data), names(breaks)), all.x=TRUE)
    data = data[order(data$starttime), ]
    data = ddply(data, .(os, test_name), fill_id)
    data$id = factor(data$id)
    data$machine = factor(data$machine)
    if ("run_num" %in% names(data)) {
        data$run_num = factor(data$run_num)
    }
    data
}

