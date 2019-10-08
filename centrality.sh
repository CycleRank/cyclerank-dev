#!/usr/bin/env bash
# shellcheck disable=SC2128
SOURCED=false && [ "$0" = "$BASH_SOURCE" ] || SOURCED=true

if ! $SOURCED; then
  echo 'Enable strict mode'
  set -euo pipefail
  IFS=$'\n\t'
fi

scratch=$(mktemp -d -t tmp.XXXXXXXXXX)
function finish {
  rm -rf "$scratch"
}
trap finish EXIT

graph="$1"
outdir="$2"

filename=$(basename -- "${graph}")
outfile="${filename%.*}.centrality.csv"

echo "Processing ${graph}...";
data=$(head -n 1 "${graph}" | tr -d $'\r');
IFS=' ' read -r nodes edges <<< "${data}"
echo "nodes: $nodes, edges: $edges"
if [ "$nodes" -gt 0 ]; then
  cp "${graph}" "${scratch}/graph.txt"
  sed -i '1d' "${scratch}/graph.txt"

  /opt/snap/snap/examples/centrality/centrality \
    "-i:${scratch}/graph.txt" \
    "-o:${scratch}/results.txt"

  cp "${scratch}/results.txt" "${outdir}/${outfile}"
fi

exit 0
