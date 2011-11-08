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
testgroups=("chrome" "nochrome" "" "chrome" "nochrome" "")
extra_testgroup=("chrome_mac" "" "" "chrome_mac" "" "")

for i in {0..5}; do
  ts=${testsuites[$i]}
  tg=${testgroups[$i]}
  tg_e=${extra_testgroup[$i]}
  output="$ts"
  params=""
  if [ ! -z $tg ]; then
    output="$ts-$tg"
    if [ ! -z $tg_e ]; then
      tg="$tg|$tg_e"
    fi
    params="--testgroup=$tg"
  fi
  echo $ts $tg $1/$output
  mkdir $1/$output
  python espull.py $common $dates $params --testsuite=$ts --output=$1/$output/$output
done;

