#!/bin/bash
url=$1
time=$2
outfile=$3

manifest=$(youtube-dl --youtube-skip-dash-manifest -f best -g $url)
ffmpeg -f hls -i $manifest -t $time -c copy -an $outfile