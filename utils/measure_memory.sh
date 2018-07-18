#!/usr/bin/env bash

# shellcheck disable=SC2128
SOURCED=false && [ "$0" = "$BASH_SOURCE" ] || SOURCED=true

if ! $SOURCED; then
  set -euo pipefail
  IFS=$'\n\t'
fi

if [ "$#" -ne 3 ]; then
	(>&2 echo "Error. Wrong number of arguments" )
	(>&2 echo "Usage: $(basename "$0") <timeout> <mem_limit> <file>")
  exit 1
fi

fullname=$(basename "$3")
filename="${fullname%.*}"

timeout "$1" ~/.scripts/limitmem.sh "$2" \
	./pageloop_back_map -d -f "$3" &>"${filename}.log" &

plpid="$!"
psrecord "$plpid" \
	--interval 2 \
	--include-children \
	--log "${filename}.psrecord.log"

exit 0
