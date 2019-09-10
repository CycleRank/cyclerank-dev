#!/usr/bin/env bash

# shellcheck disable=SC2128
SOURCED=false && [ "$0" = "$BASH_SOURCE" ] || SOURCED=true

if ! $SOURCED; then
  set -euo pipefail
  IFS=$'\n\t'
fi

# for key in "${!INFLUENZA[@]}"; do
#   echo "$key: ${INFLUENZA["$key"]}"
# done

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
      ./engineroom.sh \
        -d \
        -k 4 \
        -i "/mnt/fluiddata/cconsonni/wikilink-new-output/pagerank/${lang}wiki/20180301/2018-03-01/enwiki.wikigraph.pagerank.2018-03-01.csv" \
        -o "$(realpath .)" \
        -p "${lang}wiki.influenza.keywords.${year}-${month}-${day}.txt"
	   set +x

    )
  done
done
