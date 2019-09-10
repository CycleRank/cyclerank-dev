#!/usr/bin/env bash

# shellcheck disable=SC2128
SOURCED=false && [ "$0" = "$BASH_SOURCE" ] || SOURCED=true

if ! $SOURCED; then
  set -euo pipefail
  IFS=$'\n\t'
fi

scriptdir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

adate='20180301'
month='03'; day='01'

langs=( 'de' 'es' 'fr' 'it' 'nl' 'pl' 'ru' 'sv' );

for lang in "${langs[@]}"; do
  for year in {2001..2018}; do
    (
      cd "/mnt/fluiddata/cconsonni/wikilink-new-output/pagerank/${lang}wiki/${adate}/${year}-${month}-${day}"
      mkdir -pv influenza

      echo "Processing ${lang}wiki.influenza.keywords.${year}-${month}-${day}.txt"

      set -x
      "${scriptdir}/engineroom.sh" \
        -d \
        -k 4 \
        -i "/mnt/fluiddata/cconsonni/wikilink-new-output/pagerank/${lang}wiki/20180301/2018-03-01/enwiki.wikigraph.pagerank.2018-03-01.csv" \
        -o "$(realpath .)" \
        -p "${lang}wiki.influenza.keywords.${year}-${month}-${day}.txt"
	   set +x

    )
  done
done
