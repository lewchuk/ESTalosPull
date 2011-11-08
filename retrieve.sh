#!/bin/bash
if [ -z $1 ]; then
  echo "No output folder"
  exit
fi
mkdir $1
common="--es-server=elasticsearch1.metrics.sjc1.mozilla.com:9200 --all --analyser=comp --analyser=build --analyser=run"
dates=""
if [ ! -z $2 ]; then
  if [ ! -z $3 ]; then
  dates="--from=$2 --to=$3"
  fi
fi

testsuites=("tdhtml" "tdhtml" "tp5" "tsspider" "tsspider" "tsvg")
testgroups=("chrome|chrome_mac" "nochrome" "" "chrome|chrome_mac" "nochrome" "")

for i in {0..7}; do
  ts=${testsuites[$i]}
  tg=${testgroups[$i]}
  output="$ts"
  params=""
  if [ ! -z $tg ]; then
    output="$ts-$tg"
    params="--testgroup=$tg"
  fi
  echo $ts $tg $1/$output
  mkdir $1/$output
  python espull.py $common $dates $params --testsuite=$ts --output=$1/$output/$output
done;

