#!/bin/bash
if [ -z $1 ]; then
  echo "No output folder"
  exit
fi
mkdir $1
common="--es-server=elasticsearch1.metrics.sjc1.mozilla.com:9200 --all --analyser=comp"
dates=""
if [ ! -z $2 ]; then
  if [ ! -z $3 ]; then
  dates="--from=$2 --to=$3"
  fi
fi

testsuites=("tdhtml" "tdhtml" "ts" "tp5" "tsspider" "tsspider" "tsvg" "ts_paint")
testgroups=("chrome|chrome_mac" "nochrome" "" "" "chrome|chrome_mac" "nochrome" "" "paint")

for i in {0..7}; do
  ts=${testsuites[$i]}
  tg=${testgroups[$i]}
  output="$1/$ts.csv"
  params=""
  if [ ! -z $tg ]; then
    output="$1/$ts-$tg.csv"
    params="--testgroup=$tg"
  fi
  echo $ts $tg $output
  python espull.py $common $dates $params --testsuite=$ts --output=$output
done;

