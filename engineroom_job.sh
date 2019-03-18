#!/usr/bin/env bash

# This script does two things:
#   - Executes the looprank algorithm on the input
#   - Filters the results to get the see also.


#shellcheck disable=SC2128
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
  engineroom_job.sh [options] -i INPUT_GRAPH
                              -o OUTPUTDIR
                              -s SNAPSHOT
                              -I INDEX
                              -T TITLE
                              -p PROJECT
                              -k MAXLOOP

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
  -i INPUT_GRAPH      Absolute path of the input file.
  -o OUTPUTDIR        Absolute path of the output directory.
  -s SNAPSHOT         Absolute path of the file with the list of pages.


Options:
  -d                  Enable debug output.
  -D DATE             Date [default: infer from input graph].
  -h                  Show this help and exits.
  -k MAXLOOP          Max loop length (K) [default: 4].
  -l PROJECT          Project name [default: infer from pages list].
  -n                  Dry run, do not really launch the jobs.
  -v                  Enable verbose output.

Example:
  engineroom_job.sh  -i /home/user/pagerank/enwiki/20180301/enwiki.wikigraph.pagerank.2018-03-01.csv \\
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
dryrun_flag=false

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

while getopts ":cdD:hH:i:k:l:nN:o:p:P:q:vw:" opt; do
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
    n)
      dryrun_flag=true
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



outfile="${PROJECT}.looprank.${TITLE}.${MAXLOOP}.${DATE}.txt"

mkdir -pv "${scratch}/output"


command=("$SCRIPTDIR/pageloop_back_map_noscore" \
       "-f" "$INPUT_GRAPH" \
       "-o" "${scratch}/output/${outfile}" \
       "-s" "${idx}" \
       "-k" "$MAXLOOP" \
       )

##############################################################################
# $ ./utils/compare_seealso.py -h
# usage: compare_seealso.py [-h] [-i INPUT] [-l LINKS_DIR]
#                           [--output-dir OUTPUT_DIR] [--scores-dir SCORES_DIR]
#                           -s SNAPSHOT
#
# Compute "See also" position from LR and SSPPR.
#
# optional arguments:
#   -h, --help            show this help message and exit
#   -i INPUT, --input INPUT
#                         File with page titles [default: read from stdin].
#   -l LINKS_DIR, --links-dir LINKS_DIR
#                         Directory with the link files [default: .]
#   --output-dir OUTPUT_DIR
#                         Directory where to put output files [default: .]
#   --scores-dir SCORES_DIR
#                         Directory with the scores files [default: .]
#   -s SNAPSHOT, --snapshot SNAPSHOT
#                         Wikipedia snapshot with the id-title mapping.
#
##############################################################################

"$SCRIPTDIR/utils/compare_seealso.py" \
  --scores-dir "${scratch}/output" \
  -i "${scratch}/output/titles.txt" \
  -s "$SNAPSHOT" \
  -l "$LINKS"


exit 0
