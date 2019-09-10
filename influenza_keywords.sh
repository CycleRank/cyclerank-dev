#!/usr/bin/env bash

# shellcheck disable=SC2128
SOURCED=false && [ "$0" = "$BASH_SOURCE" ] || SOURCED=true

if ! $SOURCED; then
  set -euo pipefail
  IFS=$'\n\t'
fi



declare -A INFLUENZA=( \
['de']='Influenza' \
['en']='Influenza' \
['es']='Gripe' \
['it']='Influenza' \
['fr']='Grippe' \
['nl']='Griep' \
['pl']='Grypa' \
['ru']='Грипп' \
['sv']='Influensa' \
)

# for key in "${!INFLUENZA[@]}"; do
#   echo "$key: ${INFLUENZA["$key"]}"
# done

adate='20180301'
month='03'; day='01'

langs=( 'de' 'es' 'fr' 'it' 'nl' 'pl' 'ru' 'sv' );

for lang in "${langs[@]}"; do
  for year in {2001..2018}; do
    (
      cd "${lang}wiki/${adate}/${year}-${month}-${day}"
      mkdir -pv influenza

      title="${INFLUENZA["$lang"]}"

      echo "Page to search for ${title} (${lang})"
      echo "Processing ${lang}wiki.wikigraph.snapshot.${year}-${month}-${day}.csv ..."

      # shellcheck disable=SC2002
      \cat "${lang}wiki.wikigraph.snapshot.${year}-${month}-${day}.csv" \
        | dos2unix \
        | grep -E -i '^[0-9]+\s+'"$title"'$' \
        > "influenza/${lang}wiki.influenza.keywords.${year}-${month}-${day}.txt" \
        || true
    )
  done
done
