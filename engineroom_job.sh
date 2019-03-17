#!/usr/bin/env bash

#shellcheck disable=SC2128
SOURCED=false && [ "$0" = "$BASH_SOURCE" ] || SOURCED=true

if ! $SOURCED; then
  set -euo pipefail
  IFS=$'\n\t'
fi

# command=("./pageloop_back_map_noscore" \
#        "-f" "$INPUT_GRAPH" \
#        "-o" "${OUTPUTDIR}/${PROJECT}.looprank.${normtitle}.${MAXLOOP}.${DATE}.txt" \
#        "-s" "${idx}" \
#        "-k" "$MAXLOOP" \
#        )


###############################################################################
#  ./utils/filter_seealso_links.py -h
# usage: filter_seealso_links.py [-h] -m ID_MAP -f FILTER_LIST -s SNAPSHOT
#                                SEEALSO
#
# Extract "See also" links ids for a list of pages.
#
# positional arguments:
#   SEEALSO               File with "See also" data.
#
# optional arguments:
#   -h, --help            show this help message and exit
#   -m ID_MAP, --id-map ID_MAP
#                         File with id map.
#   -f FILTER_LIST, --filter-list FILTER_LIST
#                         File with page titles and ids to filter.
#   -s SNAPSHOT, --snapshot SNAPSHOT
#                         File with (new) page ids and page titles, i.e.,
#                         snapshot.
###############################################################################
./utils/filter_seealso_links.py \
  -f ./data/engineroom/2018-03-01/sample/enwiki.seealso.keywords.2018-03-01.sample-5000.3.txt \
  -m ./data/engineroom/2018-03-01/enwiki.idmap_o2n.2018-03-01.csv \
  -s ./data/engineroom/2018-03-01/enwiki.wikigraph.snapshot.2018-03-01.csv \
    ./data/engineroom/2018-03-01/sample/enwiki.link_snapshot.2018-03-01.csv.gz.features.csv


exit 0
