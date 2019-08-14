#!/usr/bin/env bash

#shellcheck disable=SC2128
SOURCED=false && [ "$0" = "$BASH_SOURCE" ] || SOURCED=true

if ! $SOURCED; then
  set -euo pipefail
  IFS=$'\n\t'
fi

# check if path is absolute
# https://stackoverflow.com/a/20204890/2377454
function is_abs_path() {
  local isabs=false
  local mydir="$1"

  case $mydir in
    /*)
      # 0 is true
      isabs=0
      ;;
    *)
      # 1 is false
      isabs=1
      ;;
  esac

  return $isabs
}

function check_dir() {
  local mydir="$1"
  local option="$2"

  if [[ ! -d "$mydir" ]]; then
    (>&2 echo "Error in option '$option': $mydir is not a valid directory.")
    exit 1
  fi
  if ! is_abs_path "$mydir"; then
    (>&2 echo "Error in option '$option': $mydir is not an absolute path.")
    exit 1
  fi

}

function check_file() {
  local myfile="$1"
  local option="$2"

  if [[ ! -e "$myfile" ]]; then
    (>&2 echo "Error in option '$option': $myfile is not a valid file.")
    exit 1
  fi

}

function check_posint() {
  local re='^[0-9]+$'
  local mynum="$1"
  local option="$2"

  if ! [[ "$mynum" =~ $re ]] ; then
     (echo -n "Error in option '$option': " >&2)
     (echo "must be a positive integer, got $mynum." >&2)
     exit 1
  fi

  if ! [ "$mynum" -gt 0 ] ; then
     (echo "Error in option '$option': must be positive, got $mynum." >&2)
     exit 1
  fi
}

function check_posfloat() {
  local mynum="$1"
  local option="$2"

  if ! (( $(echo "$mynum > 0" |bc -l) )); then
    (echo "Error in option '$option': must be positive, got $mynum." >&2)
  fi
}
#################### end: helpers


#################### usage
function short_usage() {
  (>&2 echo \
"Usage:
  engineroom.sh [options] -i INPUT_GRAPH
                          -o OUTPUTDIR
                          -p PAGE_LIST"
  )
}

function usage() {
  (>&2 short_usage )
  (>&2 echo \
"

Run pageloop_back_map on the graph INPUT_GRAPH for the pages listed in
PAGES_LIST and output results in OUTPUTDIR.

Arguments:
  -i INPUT_GRAPH      Absolute path of the input file.
  -o OUTPUTDIR        Absolute path of the output directory.
  -p PAGES_LIST       Absolute path of the file with the list of pages.

Options:
  -a PAGERANK_ALPHA   Damping factor (alpha) for the PageRank [default: 0.85].
  -d                  Enable debug output.
  -D DATE             Date [default: infer from input graph].
  -h                  Show this help and exits.
  -k MAXLOOP          Max loop length (K) [default: 4].
  -l PROJECT          Project name [default: infer from pages list].
  -t                  Compute PageRank on the transposed network (CheiRank).
  -v                  Enable verbose output.
  -w                  Compute PageRank on the whole network.

Example:
  engineroom.sh  -i /home/user/pagerank/enwiki/20180301/enwiki.wikigraph.pagerank.2018-03-01.csv \\
                 -o /home/user/pagerank/enwiki/20180301/ \\
                 -p enwiki.pages.txt")
}

inputgraph_unset=true
outputdir_unset=true
pageslist_unset=true
project_set=false
date_set=false
debug_flag=false
verbose_flag=false
help_flag=false
wholenetwork=false
transposed=false

INPUT_GRAPH=''
OUTPUTDIR=''
PAGES_LIST=''
PROJECT=''
MAXLOOP=4
PAGERANK_ALPHA=0.85

while getopts ":a:dD:hi:k:l:o:p:tvw" opt; do
  case $opt in
    a)
      check_posfloat "$OPTARG" '-a'

      PAGERANK_ALPHA="$(LC_ALL=C printf "%.2f" "$OPTARG")"
      ;;
    d)
      debug_flag=true
      ;;
    D)
      date_set=true

      DATE="$OPTARG"
      ;;
    h)
      help_flag=true
      ;;
    i)
      inputgraph_unset=false
      check_file "$OPTARG" '-i'

      INPUT_GRAPH="$OPTARG"
      ;;
    k)
      check_posint "$OPTARG" '-k'

      MAXLOOP="$OPTARG"
      ;;
    l)
      project_set=true

      PROJECT="$OPTARG"
      ;;
    o)
      outputdir_unset=false
      check_dir "$OPTARG" '-o'

      OUTPUTDIR="$OPTARG"
      ;;
    p)
      pageslist_unset=false
      check_file "$OPTARG" '-p'

      PAGES_LIST="$OPTARG"
      ;;
    t)
      transposed=true
      ;;
    v)
      verbose_flag=true
      ;;
    w)
      wholenetwork=true
      ;;
    \?)
      (>&2 echo "Error. Invalid option: -$OPTARG")
      exit 1
      ;;
    :)
      (>&2 echo "Error.Option -$OPTARG requires an argument.")
      exit 1
      ;;
  esac
done

if $help_flag; then
  usage
  exit 0
fi

if $inputgraph_unset; then
  (>&2 echo "Error. Option -i is required.")
  short_usage
  exit 1
fi

if $outputdir_unset; then
  (>&2 echo "Error. Option -o is required.")
  short_usage
  exit 1
fi

if $pageslist_unset; then
  (>&2 echo "Error. Option -p is required.")
  short_usage
  exit 1
fi

if ! $project_set; then
  PROJECT="$(basename "$PAGES_LIST" | \
             grep -Eo '..wiki\.' | \
             tr -d '.')" || \
  (>&2 echo "Error: could not infer project name from input. Exiting"; 
       exit 2;
  )
fi

if ! $date_set; then
  DATE="$(basename "$INPUT_GRAPH" | \
          grep -Eo '[0-9]{4}-[0-9]{2}-[0-9]{2}\.' | \
          tr -d '.')" || \
  (>&2 echo "Error: could not infer date from input. Exiting"; 
       exit 2;
  )
fi

declare -A pages

# Read file into associative array
# https://stackoverflow.com/a/25251400/2377454
while read -r line; do
    key=$(echo "$line" | awk -F$'\t' '{print $1}')
    value=$(echo "$line" | awk -F$'\t' '{print $2}')

    pages[$key]="$value"
done < "$PAGES_LIST"

if $debug_flag; then
  function echodebug() {
    (>&2 echo -en "[$(date '+%F_%H:%M:%S')][debug]\\t")
    (>&2 echo "$@" 1>&2)
  }
else
  function echodebug() { true; }
fi

#################### debug info
echodebug "Arguments:"
echodebug "  * INPUT_GRAPH (-i): $INPUT_GRAPH"
echodebug "  * OUTPUTDIR (-o): $OUTPUTDIR"
echodebug "  * PAGES_LIST  (-p): $PAGES_LIST"
echodebug

echodebug "Options:"
echodebug "  * PAGERANK_ALPHA (-a): $PAGERANK_ALPHA"
echodebug "  * debug_flag (-d): $debug_flag"
echodebug "  * DATE (-D): $DATE"
echodebug "  * MAXLOOP (-k): $MAXLOOP"
echodebug "  * PROJECT (-l): $PROJECT"
echodebug "  * transposed (-t): $transposed"
echodebug "  * verbose_flag (-v): $verbose_flag"
echodebug "  * wholenetwork (-w): $wholenetwork"
echodebug

echodebug "Pages from $PROJECT ($DATE):"
for title in "${!pages[@]}"; do
  idx="${pages[$title]}"
  echodebug "* $title ($idx)"
done
#################### end: debug info

for title in "${!pages[@]}"; do
  echo "Processing $title ($idx) ..."
  idx="${pages[$title]}"
  normtitle="${title/ /_}"

  if $transposed; then
    logfile="${OUTPUTDIR}/${PROJECT}.cheir.a${PAGERANK_ALPHA}.${normtitle}.${MAXLOOP}.${DATE}.log"
  else
    logfile="${OUTPUTDIR}/${PROJECT}.ssppr.a${PAGERANK_ALPHA}.${normtitle}.${MAXLOOP}.${DATE}.log"
  fi

  echo "Logging to ${logfile}"

  wholenetwork_flag=''
  if $wholenetwork; then
    wholenetwork_flag='-w'
  fi

  transposed_flag=''
  if $transposed; then
    outfile="${PROJECT}.cheir.a${PAGERANK_ALPHA}.${normtitle}.${MAXLOOP}.${DATE}.txt"
    transposed_flag='-t'
  else
    outfile="${PROJECT}.ssppr.a${PAGERANK_ALPHA}.${normtitle}.${MAXLOOP}.${DATE}.txt"
  fi


  command=("./ssppr" \
           "-a" "$PAGERANK_ALPHA" \
           "-d" \
           "-f" "$INPUT_GRAPH" \
           "-o" "${OUTPUTDIR}/${outfile}" \
           "-s" "${idx}" \
           "-k" "$MAXLOOP" \
           ${transposed_flag[@]:+"${transposed_flag[@]}"} \
           ${wholenetwork_flag[@]:+"${wholenetwork_flag[@]}"}
           )

  if $debug_flag || $verbose_flag; then set -x; fi
  if $debug_flag; then
    "${command[@]}" | tee "${logfile}"
  else
    "${command[@]}" >  "${logfile}"
  fi
  if $debug_flag || $verbose_flag; then set +x; fi

done
