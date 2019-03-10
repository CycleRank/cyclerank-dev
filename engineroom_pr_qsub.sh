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
  -c PBS_NCPUS        Number of PBS cpus to request (needs also -n and -P to be specified).
  -d                  Enable debug output.
  -D DATE             Date [default: infer from input graph].
  -h                  Show this help and exits.
  -H PBS_HOST         PBS host to run on.
  -k MAXLOOP          Max loop length (K) [default: 4].
  -l PROJECT          Project name [default: infer from pages list].
  -n                  Dry run, do not really launch the jobs.
  -N PBS_NODES        Number of PBS nodes to request (needs also -c  and -P to be specified).
  -P PBS_PPN          Number of PBS processors per node to request (needs also -n  and -P to be specified).
  -q PBS_QUEUE        PBS queue name [default: cpuq].
  -v                  Enable verbose output.
  -w                  Compute the pagerank on the whole network.
  -W PBS_WALLTIME     Max walltime for the job, a time period formatted as hh:mm:ss.

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

INPUT_GRAPH=''
OUTPUTDIR=''
PAGES_LIST=''
PROJECT=''
MAXLOOP=4

# PBS
pbs_nodes_set=false
pbs_ppn_set=false
pbs_ncpus_set=false

PBS_QUEUE='cpuq'
PBS_NCPUS=''
PBS_NODES=''
PBS_PPN=''
PBS_WALLTIME=''
PBS_HOST=''

while getopts ":dD:hi:k:l:o:p:vw" opt; do
  case $opt in
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
echodebug "  * debug_flag (-d): $debug_flag"
echodebug "  * verbose_flag (-v): $verbose_flag"
echodebug "  * DATE (-D): $DATE"
echodebug "  * PROJECT (-l): $PROJECT"
echodebug "  * MAXLOOP (-k): $MAXLOOP"
echodebug "  * wholenetwork (-w): $wholenetwork"
echodebug

echodebug "Pages from $PROJECT ($DATE):"
for title in "${!pages[@]}"; do
  idx="${pages[$title]}"
  echodebug "* $title ($idx)"
done
#################### end: debug info

declare -a pbsoptions
if [ -n "$PBS_WALLTIME" ]; then
  pbsoptions+=('-l' "walltime=$PBS_WALLTIME")
fi

if [ -n "$PBS_NODES" ]; then
  pbsoptions+=('-l' "nodes=$PBS_NODES:ncpus=$PBS_NCPUS:ppn=$PBS_PPN")
fi

if [ -n "$PBS_HOST" ]; then
  pbsoptions+=('-l' "host=$PBS_HOST")
fi

for title in "${!pages[@]}"; do
  echo "Processing $title ($idx) ..."
  idx="${pages[$title]}"
  normtitle="${title/ /_}"
  pbsjobname="${idx}"

  logfile="${OUTPUTDIR}/${PROJECT}.ssppr.${normtitle}.${MAXLOOP}.${DATE}.log"
  echo "Logging to ${logfile}"

  wholenetwork_flag=''
  if $wholenetwork; then
    wholenetwork_flag='-w'
  fi

  command=("./ssppr" \
           "-d" \
           "-f" "$INPUT_GRAPH" \
           "-o" "${OUTPUTDIR}/${PROJECT}.ssppr.${normtitle}.${MAXLOOP}.${DATE}.txt" \
           "-s" "${idx}" \
           "-k" "$MAXLOOP" \
           ${wholenetwork_flag[@]:+"${wholenetwork_flag[@]}"}
           )

  wrap_run \
  qsub -N "$pbsjobname" -q "$PBS_QUEUE" ${pbsoptions[@]:+"${pbsoptions[@]}"} -- \
    "${command[@]}"
  if $debug_flag || $verbose_flag; then set +x; fi

  if $debug_flag || $verbose_flag; then set +x; fi

done
