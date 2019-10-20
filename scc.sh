#!/usr/bin/env bash
# shellcheck disable=SC2128
SOURCED=false && [ "$0" = "$BASH_SOURCE" ] || SOURCED=true

if ! $SOURCED; then
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
outprefix="${filename%.*}.concomp"

echo "Processing ${graph}...";
data=$(head -n 1 "${graph}" | tr -d $'\r');
IFS=' ' read -r nodes edges <<< "${data}"
echo "nodes: $nodes, edges: $edges"
if [ "$nodes" -gt 0 ]; then
  cp "${graph}" "${scratch}/${filename}"
  sed -i '1d' "${scratch}/${filename}"

  /opt/snap/snap/examples/concomp/concomp \
    "-i:${scratch}/${filename}" \
    "-o:${scratch}/${outprefix}"

  cp "${scratch}/${outprefix}"* "${outdir}/"
fi

exit 0
