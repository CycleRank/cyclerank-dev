#!/usr/bin/env bash

title="$1"
idx="$2"

echo "Processing title: $title - idx: $idx";

~/work/engineroom/pageloop/code/pageloop_back_map_noscore \
  -d \
  -k 4 \
  -s "$idx" \
  -f ../enwiki.wikigraph.pagerank.2018-03-01.csv \
  -o "enwiki.looprank.$title.4.2018-03-01.txt"

~/work/engineroom/pageloop/code/ssppr \
  -d \
  -w \
  -s "$idx" \
  -f ../enwiki.wikigraph.pagerank.2018-03-01.csv \
  -o "enwiki.ssppr.$title.wholenetwork.2018-03-01.txt"

~/work/engineroom/pageloop/code/ssppr \
  -d \
  -k 4 \
  -s "$idx" \
  -f ../enwiki.wikigraph.pagerank.2018-03-01.csv \
  -o "enwiki.ssppr.$title.4.2018-03-01.txt"

~/work/engineroom/pageloop/code/ssppr \
  -d \
  -t \
  -w \
  -s "$idx" \
  -f ../enwiki.wikigraph.pagerank.2018-03-01.csv \
  -o "enwiki.cheir.$title.wholenetwork.2018-03-01.txt"

~/work/engineroom/pageloop/code/ssppr \
  -d \
  -t \
  -k 4 \
  -s "$idx" \
  -f ../enwiki.wikigraph.pagerank.2018-03-01.csv \
  -o "enwiki.cheir.$title.4.2018-03-01.txt"

~/work/engineroom/pageloop/code/utils/2Drank.py \
  -c "enwiki.cheir.$title.4.2018-03-01.txt" \
  -s "enwiki.ssppr.$title.4.2018-03-01.txt"

~/work/engineroom/pageloop/code/utils/wikipedia_results.py \
  -i "enwiki.cheir.$title.4.2018-03-01.txt" \
  -s ../enwiki.wikigraph.snapshot.2018-03-01.csv \
  --sort score \
  -r \
    > "enwiki.cheir.$title.4.2018-03-01.results.txt"

~/work/engineroom/pageloop/code/utils/wikipedia_results.py \
  -i "enwiki.2Drank.$title.4.2018-03-01.txt" \
  -s ../enwiki.wikigraph.snapshot.2018-03-01.csv \
  --sort score \
  -r \
    > "enwiki.2Drank.$title.4.2018-03-01.results.txt"

~/work/engineroom/pageloop/code/utils/2Drank.py \
  -c "enwiki.cheir.$title.wholenetwork.2018-03-01.txt" \
  -s "enwiki.ssppr.$title.wholenetwork.2018-03-01.txt"

~/work/engineroom/pageloop/code/utils/wikipedia_results.py \
  -i "enwiki.cheir.$title.wholenetwork.2018-03-01.txt" \
  -s ../enwiki.wikigraph.snapshot.2018-03-01.csv \
  --sort score \
  -r \
    > "enwiki.cheir.$title.wholenetwork.2018-03-01.results.txt"

~/work/engineroom/pageloop/code/utils/wikipedia_results.py \
  -i "enwiki.2Drank.$title.wholenetwork.2018-03-01.txt" \
  -s ../enwiki.wikigraph.snapshot.2018-03-01.csv \
  --sort score \
  -r \
    > "enwiki.2Drank.$title.wholenetwork.2018-03-01.results.txt"
