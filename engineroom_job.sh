#!/usr/bin/env bash
#PBS -V
#PBS -l walltime=01:00:00
#PBS -l nodes=1:ncpus=1:ppn=1
#PBS -q short_cpuQ

# This script does two things:
#   - Executes the looprank algorithm on the input
#   - Filters the results to get the see also.

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

function check_int() {
  local re='^[0-9]+$'
  local mynum="$1"
  local option="$2"

  if ! [[ "$mynum" =~ $re ]] ; then
     (echo -n "Error in option '$option': " >&2)
     (echo "must be a positive integer, got $mynum." >&2)
     exit 1
  fi

  if ! [ "$mynum" -ge 0 ] ; then
     (echo "Error in option '$option': must be positive, got $mynum." >&2)
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
                              -l LINKS_DIR
                              -I INDEX
                              -T TITLE
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
  -l LINKS_DIR
  -I INDEX
  -T TITLE


Options:
  -d                  Enable debug output.
  -D DATE             Date [default: infer from input graph].
  -h                  Show this help and exits.
  -k MAXLOOP          Max loop length (K) [default: 4].
  -K                  Keep temporary files.
  -p PROJECT          Project name [default: infer from input graph].
  -P PYTHON_VERSION   Python version [default: 3.6].
  -w                  Compute the pagerank on the whole network.
  -n                  Dry run, do not really launch the jobs.
  -v                  Enable verbose output.
  -V VENV_PATH        Absolute path of the virtualenv directory [default: \$PWD/looprank3].

Example:
  engineroom_job.sh  -i /home/user/pagerank/enwiki/20180301/enwiki.wikigraph.pagerank.2018-03-01.csv \\
                     -o /home/user/pagerank/enwiki/20180301/ \\
                     -p enwiki.pages.txt")
}


inputgraph_unset=true
outputdir_unset=true
snapshot_unset=true
linksdir_unset=true
index_unset=true
title_unset=true
wholenetwork=false

project_set=false
date_set=false
debug_flag=false
verbose_flag=false
help_flag=false
dryrun_flag=false
keeptmp_flag=false

VENV_PATH="$PWD/looprank3"
PYTHON_VERSION='3.6'

INPUT_GRAPH=''
OUTPUTDIR=''
LINKS_DIR=''
DATE=''
PROJECT=''
MAXLOOP=4

while getopts ":dD:hi:I:k:Kl:no:p:P:s:T:vV:w" opt; do
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
    I)
      index_unset=false
      check_int "$OPTARG" '-I'

      INDEX="$OPTARG"
      ;;
    k)
      check_posint "$OPTARG" '-k'

      MAXLOOP="$OPTARG"
      ;;
    K)
      keeptmp_flag=true
      ;;
    l)
      linksdir_unset=false
      check_dir "$OPTARG" '-l'

      LINKS_DIR="$OPTARG"
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
      project_set=true

      PROJECT="$OPTARG"
      ;;
    P)
      PYTHON_VERSION="$OPTARG"
      ;;
    s)
      snapshot_unset=false
      check_file "$OPTARG" '-s'

      SNAPSHOT="$OPTARG"
      ;;
    T)
      title_unset=false

      TITLE="$OPTARG"
      ;;
    v)
      verbose_flag=true
      ;;
    V)
      check_dir "$OPTARG" '-V'

      VENV_PATH="$OPTARG"
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

if $index_unset; then
  (>&2 echo "Error. Option -I is required.")
  short_usage
  exit 1
fi

if $title_unset; then
  (>&2 echo "Error. Option -T is required.")
  short_usage
  exit 1
fi

if ! $date_set; then
  DATE="$(basename "$INPUT_GRAPH" | \
          grep -Eo '[0-9]{4}-[0-9]{2}-[0-9]{2}\.' | \
          tr -d '.')" || \
  (>&2 echo "Error: could not infer date from input. Exiting";
       exit 2;
  )
fi

if ! $project_set; then
  PROJECT="$(basename "$INPUT_GRAPH" | \
             grep -Eo '..wiki\.' | \
             tr -d '.')" || \
  (>&2 echo "Error: could not infer project name from input. Exiting";
       exit 2;
  )
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

function safe_head() {
  local num="$1"
  local input="$2"

  if [ "$num" -gt 0 ]; then
    head -n "$num" "$input" 
  else
    cat "$input"
  fi
}
#################### end: utils

#################### debug info
echodebug "Arguments:"
echodebug "  * INPUT_GRAPH (-i): $INPUT_GRAPH"
echodebug "  * OUTPUTDIR (-o): $OUTPUTDIR"
echodebug "  * SNAPSHOT (-s): $SNAPSHOT"
echodebug "  * LINKS_DIR (-l): $LINKS_DIR"
echodebug "  * INDEX (-I): $INDEX"
echodebug "  * TITLE (-T): $TITLE"
echodebug

echodebug "Options:"
echodebug "  * debug_flag (-d): $debug_flag"
echodebug "  * DATE (-D): $DATE"
echodebug "  * MAXLOOP (-k): $MAXLOOP"
echodebug "  * PROJECT (-p): $PROJECT"
echodebug "  * PYTHON_VERSION (-P): $PYTHON_VERSION"
echodebug "  * dryrun_flag (-n): $dryrun_flag"
echodebug "  * verbose_flag (-v): $verbose_flag"
echodebug "  * VENV_PATH (-V): $VENV_PATH"
echodebug "  * wholenetwork (-w): $wholenetwork"
echodebug

#################### end: debug info

########## start job
echo "job running on: $(hostname)"

set +ue
echodebug "activate virtualenv: source '$VENV_PATH/bin/activate'"
# shellcheck disable=SC1090
source "$VENV_PATH/bin/activate"
echodebug "... done!"
set -ue

reference_python="$(command -v "python${PYTHON_VERSION}")"
echodebug "reference Python path: $reference_python"

if [ -z "$reference_python" ]; then
  (>&2 echo "Error. No reference Python found for version: $PYTHON_VERSION")
  exit 1
fi


scratch=$(mktemp -d -t tmp.engineroom_job.XXXXXXXXXX)
if ! $keeptmp_flag; then
  function finish {
    rm -rf "$scratch"
  }
  trap finish EXIT
fi

# create temporary output  directory
tmpoutdir="${scratch}/output" 
mkdir -p "${tmpoutdir}"
echodebug "Created ${tmpoutdir}"

# convert spaces to underscores
NORMTITLE="${TITLE/ /_}"

# verbosity flag
verbosity_flag=''
if $debug_flag; then
  verbosity_flag='-d'
elif $verbose_flag; then
  verbosity_flag='-v'
fi

##### LoopRank
outfileLR="${PROJECT}.looprank.${NORMTITLE}.${MAXLOOP}.${DATE}.txt"
logfileLR="${OUTPUTDIR}/${PROJECT}.looprank.${NORMTITLE}.${MAXLOOP}.${DATE}.log"


commandLR=("$SCRIPTDIR/pageloop_back_map_noscore" \
           "-f" "${INPUT_GRAPH}" \
           "-o" "${tmpoutdir}/${outfileLR}" \
           "-s" "${INDEX}" \
           "-k" "${MAXLOOP}" \
           ${verbosity_flag:+"$verbosity_flag"}
           )

if $debug_flag || $verbose_flag; then set -x; fi
if $debug_flag; then
  "${commandLR[@]}" | tee "${logfileLR}"
elif $verbose_flag; then
  "${commandLR[@]}" >  "${logfileLR}"
else
  "${commandLR[@]}"
fi
if $debug_flag || $verbose_flag; then set +x; fi

# Compute LoopRank scores
scorefileLR="${PROJECT}.looprank.${NORMTITLE}.${MAXLOOP}.${DATE}.scores.txt"
inputfileLR="${tmpoutdir}/${outfileLR}"

echodebug "encoding: $(python3 -c 'import locale; print(locale.getpreferredencoding(False))')"

python3 "${SCRIPTDIR}/utils/compute_scores.py" \
  -o "${tmpoutdir}/${scorefileLR}" \
    "${inputfileLR}"


##### Single-source Personalized PageRank
##############################################################################
outfileSSPPR="${PROJECT}.ssppr.${NORMTITLE}.${MAXLOOP}.${DATE}.txt"
logfileSSPPR="${OUTPUTDIR}/${PROJECT}.ssppr.${NORMTITLE}.${MAXLOOP}.${DATE}.log"

wholenetwork_flag=''
if $wholenetwork; then
  wholenetwork_flag='-w'
fi

commandSSPPR=("$SCRIPTDIR/ssppr" \
              "-f" "${INPUT_GRAPH}" \
              "-o" "${tmpoutdir}/${outfileSSPPR}" \
              "-s" "${INDEX}" \
              "-k" "${MAXLOOP}" \
              ${verbosity_flag:+"$verbosity_flag"} \
              ${wholenetwork_flag[@]:+"${wholenetwork_flag[@]}"}
              )

if $debug_flag || $verbose_flag; then set -x; fi
if $debug_flag; then
  "${commandSSPPR[@]}" | tee "${logfileSSPPR}"
else
  "${commandSSPPR[@]}" >  "${logfileSSPPR}"
fi
if $debug_flag || $verbose_flag; then set +x; fi

##### Compare See Also
##############################################################################

# save page title in scratch/title.txt
echo "${NORMTITLE}" >> "${scratch}/titles.txt"
echodebug "${NORMTITLE}"

if $debug_flag || $verbose_flag; then set -x; fi

python3 "$SCRIPTDIR/utils/compare_seealso.py" \
  -i "${scratch}/titles.txt" \
  -l "$LINKS_DIR" \
  --output-dir "$OUTPUTDIR" \
  --scores-dir "${tmpoutdir}" \
  -s "$SNAPSHOT"

if $debug_flag || $verbose_flag; then set +x; fi

comparefileSSPPR="${PROJECT}.ssppr.${NORMTITLE}.${DATE}.compare_lr-pr.txt"
maxrowSSPPR="$(LC_ALL=C \
  awk 'BEGIN{a=0}{if ($1>0+a) a=$1} END{print a}' \
    "${OUTPUTDIR}/${comparefileSSPPR}"
  )"

# outfileLR="${PROJECT}.looprank.${NORMTITLE}.${MAXLOOP}.${DATE}.txt"
# scorefileLR="${PROJECT}.looprank.${NORMTITLE}.${MAXLOOP}.${DATE}.scores.txt"
# outfileSSPPR="${PROJECT}.ssppr.${NORMTITLE}.${MAXLOOP}.${DATE}.txt"

LC_ALL=C sort -t$'\t' -k2 -r -n "${tmpoutdir}/${outfileSSPPR}" \
  > "${tmpoutdir}/${outfileSSPPR}.sorted"

cp "${tmpoutdir}/${outfileLR}" "${OUTPUTDIR}/${outfileLR}"
cp "${tmpoutdir}/${scorefileLR}" "${OUTPUTDIR}/${scorefileLR}"
safe_head "$((maxrowSSPPR+1))" "${tmpoutdir}/${outfileSSPPR}.sorted" > "${OUTPUTDIR}/${outfileSSPPR}"

echo "Done processing ${NORMTITLE}!"
(>&2 echo "Done processing ${NORMTITLE}!" )

exit 0
