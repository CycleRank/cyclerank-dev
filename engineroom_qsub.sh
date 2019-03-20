#!/usr/bin/env bash

#shellcheck disable=SC2128
SOURCED=false && [ "$0" = "$BASH_SOURCE" ] || SOURCED=true

if ! $SOURCED; then
  set -euo pipefail
  IFS=$'\n\t'
fi

SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

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
  engineroom_qsub.sh [options] -i INPUT_GRAPH
                               -o OUTPUTDIR
                               -s SNAPSHOT
                               -l LINKS_DIR
                               -I PAGES_LIST
  "
  )
}

function usage() {
  (>&2 short_usage )
  (>&2 echo \
"

Run pageloop_back_map on the graph INPUT_GRAPH for the pages listed in
PAGES_LIST and output results in OUTPUTDIR.

Arguments:
  -i INPUT_GRAPH          Absolute path of the input file.
  -o OUTPUTDIR            Absolute path of the output directory.
  -s SNAPSHOT             Absolute path of the file with the graph snapshot.
  -l LINKS_DIR            Absolute path of the directory with the link files .
  -I PAGES_LIST           Absolute path of the file with the list of pages.


Options:
  -c PBS_NCPUS            Number of PBS cpus to request (needs also -n and -P to be specified).
  -d                      Enable debug output.
  -D DATE                 Date [default: infer from input graph].
  -h                      Show this help and exits.
  -H PBS_HOST             PBS host to run on.
  -k MAXLOOP              Max loop length (K) [default: 4].
  -M MAX_JOBS_PER_BATCH   Nunber of jobs to submit in batch [default: 30].
  -n                      Dry run, do not really launch the jobs.
  -N PBS_NODES            Number of PBS nodes to request (needs also -c  and -P to be specified).
  -p PROJECT              Project name [default: infer from pages list].
  -P PBS_PPN              Number of PBS processors per node to request (needs also -n  and -P to be specified).
  -q PBS_QUEUE            PBS queue name [default: cpuq].
  -S SLEEP_PER_BATCH      Sleeping time in seconds between batches [default: 1800].
  -v                      Enable verbose output.
  -V VENV_PATH            Absolute path of the virtualenv directory [default: \$PWD/wikidump].
  -x PYTHON_VERSION       Python version [default: 3.6].
  -w PBS_WALLTIME         Max walltime for the job, a time period formatted as hh:mm:ss.
  -W                      Compute the pagerank on the whole network.

Example:
  engineroom_qsub.sh")
}

inputgraph_unset=true
outputdir_unset=true
snapshot_unset=true
linksdir_unset=true
pageslist_unset=true

project_set=false
date_set=false
debug_flag=false
verbose_flag=false
help_flag=false
dryrun_flag=false
wholenetwork=false

INPUT_GRAPH=''
OUTPUTDIR=''
PAGES_LIST=''
PROJECT=''
MAXLOOP=4

VENV_PATH="$PWD/looprank3"
PYTHON_VERSION='3.6'

# PBS
pbs_ncpus_set=false
pbs_nodes_set=false
pbs_ppn_set=false

PBS_QUEUE='cpuq'
PBS_NCPUS=''
PBS_NODES=''
PBS_PPN=''
PBS_WALLTIME=''
PBS_HOST=''

MAX_JOBS_PER_BATCH=30
SLEEP_PER_BATCH=1800

while getopts ":cdD:hH:i:I:k:l:M:nN:o:p:P:q:s:S:vV:x:w:W" opt; do
  case $opt in
    c)
      check_posint "$OPTARG" '-c'

      pbs_ncpus_set=true
      PBS_NCPUS="$OPTARG"
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
    H)
      PBS_HOST="$OPTARG"
      ;;
    i)
      inputgraph_unset=false
      check_file "$OPTARG" '-i'

      INPUT_GRAPH="$OPTARG"
      ;;
    I)
      pageslist_unset=false
      check_file "$OPTARG" '-I'

      PAGES_LIST="$OPTARG"
      ;;
    k)
      check_posint "$OPTARG" '-k'

      MAXLOOP="$OPTARG"
      ;;
    l)
      linksdir_unset=false
      check_dir "$OPTARG" '-l'

      LINKS_DIR="$OPTARG"
      ;;
    M)
      check_posint "$OPTARG" '-M'

      MAX_JOBS_PER_BATCH="$OPTARG"
      ;;
    n)
      dryrun_flag=true
      ;;
    N)
      check_posint "$OPTARG" '-n'

      pbs_nodes_set=true
      PBS_NODES="$OPTARG"
      ;;
    o)
      outputdir_unset=false
      check_dir "$OPTARG" '-o'

      OUTPUTDIR="$OPTARG"
      ;;
    p)
      project_set=true

      PROJECT="$OPTARG"
      ;;
    P)
      check_posint "$OPTARG" '-P'

      pbs_ppn_set=true
      PBS_PPN="$OPTARG"
      ;;
    q)
      PBS_QUEUE="$OPTARG"
      ;;
    s)
      snapshot_unset=false
      check_file "$OPTARG" '-s'

      SNAPSHOT="$OPTARG"
      ;;
    S)
      SLEEP_PER_BATCH="$OPTARG"
      ;;
    v)
      verbose_flag=true
      ;;
    V)
      check_dir "$OPTARG" '-v'

      VENV_PATH="$OPTARG"
      ;;
    x)
      PYTHON_VERSION="$OPTARG"
      ;;
    w)
      PBS_WALLTIME="$OPTARG"
      ;;
    W)
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

if $snapshot_unset; then
  (>&2 echo "Error. Option -s is required.")
  short_usage
  exit 1
fi

if $linksdir_unset; then
  (>&2 echo "Error. Option -l is required.")
  short_usage
  exit 1
fi

if $pageslist_unset; then
  (>&2 echo "Error. Option -I is required.")
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

# PBS nodes, PBS ncpus and PBS ppn must be set all togheter.
# A xor B == ( A or B ) && ( not ( A && B ) )
if ($pbs_nodes_set || $pbs_ncpus_set) && \
    ! ($pbs_nodes_set && $pbs_ncpus_set); then
  (>&2 echo "Options -c, -n, -P must be specified togheter.")
  short_usage
  exit 1
fi

if ($pbs_nodes_set || $pbs_ppn_set) && \
    ! ($pbs_nodes_set && $pbs_ppn_set); then
  (>&2 echo "Options -c, -n, -P must be specified togheter.")
  short_usage
  exit 1
fi

#################### utils
if $debug_flag; then
  function echodebug() {
    (>&2 echo -en "[$(date '+%F_%H:%M:%S')][debug]\\t")
    (>&2 echo "$@" 1>&2)
  }
else
  function echodebug() { true; }
fi

if $dryrun_flag; then
  function wrap_run() { 
    ( echo -en "[dry run]\\t" )
    ( echo "$@" )
  }
else
  function wrap_run() { "$@"; }
fi
#################### end: utils

#################### debug info
echodebug "Arguments:"
echodebug "  * INPUT_GRAPH (-i): $INPUT_GRAPH"
echodebug "  * OUTPUTDIR (-o): $OUTPUTDIR"
echodebug "  * SNAPSHOT (-s): $SNAPSHOT"
echodebug "  * LINKS_DIR (-l): $LINKS_DIR"
echodebug "  * PAGES_LIST (-I): $PAGES_LIST"
echodebug

echodebug "Options:"
echodebug "  * PBS_NCPUS (-c): $PBS_NCPUS"
echodebug "  * debug_flag (-d): $debug_flag"
echodebug "  * PBS_HOST (-H): $PBS_HOST"
echodebug "  * DATE (-D): $DATE"
echodebug "  * MAXLOOP (-k): $MAXLOOP"
echodebug "  * PROJECT (-l): $PROJECT"
echodebug "  * MAX_JOBS_PER_BATCH (-M): $MAX_JOBS_PER_BATCH"
echodebug "  * PBS_NODES (-n): $PBS_NODES"
echodebug "  * dryrun_flag (-N): $dryrun_flag"
echodebug "  * PBS_PPN (-P): $PBS_PPN"
echodebug "  * PBS_QUEUE (-q): $PBS_QUEUE"
echodebug "  * SLEEP_PER_BATCH (-S): $SLEEP_PER_BATCH"
echodebug "  * verbose_flag (-v): $verbose_flag"
echodebug "  * VENV_PATH (-V): $VENV_PATH"
echodebug "  * PYTHON_VERSION (-x): $PYTHON_VERSION"
echodebug "  * PBS_WALLTIME (-w): $PBS_WALLTIME"
echodebug "  * wholenetwork (-W): $wholenetwork"
echodebug
#################### end: debug info

declare -A pages

# Read file into associative array
# https://stackoverflow.com/a/25251400/2377454
count_pages=0
while read -r line; do
  key=$(echo "$line" | awk -F$'\t' '{print $1}')
  value=$(echo "$line" | awk -F$'\t' '{print $2}')

  echodebug -ne "-> processed pages: $count_pages\033[0K\r"

  pages[$key]="$value"
  count_pages=$((count_pages+1))
done < "$PAGES_LIST"
echodebug

#################### debug info
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

counter=0
for title in "${!pages[@]}"; do
  echo "Processing $title ($idx) ..."
  idx="${pages[$title]}"
  normtitle="${title/ /_}"

  pbsjobname="ngi_${MAXLOOP}_${idx}"

  logfile="${OUTPUTDIR}/${PROJECT}.looprank.${normtitle}.${MAXLOOP}.${DATE}.log"
  echo "Logging to ${logfile}"

  ############################################################################
  # $ ./engineroom_job.sh -h
  # Usage:
  #   engineroom_job.sh [options] -i INPUT_GRAPH
  #                               -o OUTPUTDIR
  #                               -s SNAPSHOT
  #                               -l LINKS_DIR
  #                               -I INDEX
  #                               -T TITLE
  #
  #
  # Run pageloop_back_map on the graph INPUT_GRAPH for the pages listed in
  # PAGES_LIST and output results in OUTPUTDIR.
  #
  # Arguments:
  #   -i INPUT_GRAPH      Absolute path of the input file.
  #   -o OUTPUTDIR        Absolute path of the output directory.
  #   -s SNAPSHOT         Absolute path of the file with the list of pages.
  #   -l LINKS_DIR
  #   -I INDEX
  #   -T TITLE
  #
  #
  # Options:
  #   -d                  Enable debug output.
  #   -D DATE             Date [default: infer from input graph].
  #   -h                  Show this help and exits.
  #   -k MAXLOOP          Max loop length (K) [default: 4].
  #   -K                  Keep temporary files.
  #   -p PROJECT          Project name [default: infer from input graph].
  #   -w                  Compute the pagerank on the whole network.
  #   -n                  Dry run, do not really launch the jobs.
  #   -v                  Enable verbose output.
  #
  # Example:
  #   engineroom_job.sh  -i /home/user/pagerank/enwiki/20180301/enwiki.wikigraph.pagerank.2018-03-01.csv \
  #                      -o /home/user/pagerank/enwiki/20180301/ \
  #                      -p enwiki.pages.txt
  ############################################################################
  command=("${SCRIPTDIR}/engineroom_job.sh" \
           "-k" "$MAXLOOP" \
           "-x" "$PYTHON_VERSION" \
           "-V" "$VENV_PATH" \
           "-i" "$INPUT_GRAPH" \
           "-o" "${OUTPUTDIR}" \
           "-s" "${SNAPSHOT}" \
           "-l" "${LINKS_DIR}"
           "-I" "${idx}"
           "-T" "${normtitle}"
           )

  # qsub -N <pbsjobname> -q cpuq [psb_options] -- \
  #   <scriptdir>/engineroom_job.sh ...

  if $debug_flag; then { set -x; }  fi
  wrap_run \
  qsub \
    -N "$pbsjobname" \
    -q "$PBS_QUEUE" \
    ${pbsoptions[@]:+"${pbsoptions[@]}"} -- \
      "${command[@]}"
  if $debug_flag || $verbose_flag; then set +x; fi

  counter=$((counter+1))

  echodebug "counter: $counter"
  echo "Sleep for $SLEEP_PER_BATCH seconds... "
  if [[ $((counter % MAX_JOBS_PER_BATCH )) == 0 ]]; then
    secs="$SLEEP_PER_BATCH"
    waitsec=1
    while [ "$secs" -gt 0 ]; do
     echo -ne "$secs\033[0K\r"
     sleep "$waitsec"
     secs=$((secs-waitsec))
    done
  fi
done
