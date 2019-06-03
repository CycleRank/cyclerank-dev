#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import csv
import math
import argparse
import pathlib
from collections import defaultdict

NDIGITS = 5

def linear_score(scores, cycle):
    csize = len(cycle)
    for node in cycle:
        scores[node] += 1.0/csize


def square_score(scores, cycle):
    csize = len(cycle)
    for node in cycle:
        scores[node] += 1.0/(csize*csize)


def cube_score(scores, cycle):
    csize = len(cycle)
    for node in cycle:
        scores[node] += 1.0/(csize*csize*csize)


def cube_score(scores, cycle):
    csize = len(cycle)
    for node in cycle:
        scores[node] += 1.0/(csize*math.log(csize))


def nlogn_score(scores, cycle):
    csize = len(cycle)
    for node in cycle:
        scores[node] += 1.0/(csize*math.log(csize))


def expe_score(scores, cycle):
    csize = len(cycle)
    for node in cycle:
        scores[node] += math.exp(-csize)


def exp10_score(scores, cycle):
    csize = len(cycle)
    for node in cycle:
        scores[node] += math.pow(10, -csize)


SCORING_FUNCTIONS = {
'linear': linear_score,		# 1/10^n
'square': square_score,		# 1/n^2
'cube': cube_score,			# 1/n^3
'nlogn': nlogn_score,		# 1/n*log(n)
'expe': expe_score,			# 1/(e^n)
'exp10': exp10_score 		# 1(10^n)
}


# Processing non-UTF-8 Posix filenames using Python pathlib?
# https://stackoverflow.com/a/45724695/2377454
def safe_path(path: pathlib.Path) -> pathlib.Path:
    encoded_path = path.as_posix().encode('utf-8')
    return pathlib.Path(os.fsdecode(encoded_path))


if __name__ == '__main__':
    desc = 'Assign score to pageloop cyles.'
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('FILE',
                        type=pathlib.Path,
                        help='Input file (w/ pageloop cycles).')
    parser.add_argument('-k', '--maxloop',
                        type=int,
                        dest='K',
                        help='Limit cycles to this length (K) '
                             '[default: No limit].')
    parser.add_argument('-o', '--output',
                        type=pathlib.Path,
                        help='output file name [default: stdout].')
    parser.add_argument('-f', '--scoring-function',
                        choices=list(SCORING_FUNCTIONS.keys()),
                        default='linear',
                        help='Scoring function [default: linear]')

    args = parser.parse_args()

    infile = args.FILE
    output = args.output
    K = args.K
    scoring_function = SCORING_FUNCTIONS[args.scoring_function]

    scores = defaultdict(float)
    with safe_path(infile).open('r', encoding='UTF-8') as infp:
        reader = csv.reader(infp, delimiter=' ')

        for cycle in reader:
            csize = len(cycle)
            if K is not None and csize > K: continue

            cycle = [int(node) for node in cycle]

            scoring_function(scores, cycle)

    outfile = None
    if output is None:
        outfile = sys.stdout
    else:
        outfile = safe_path(output).open('w+', encoding='UTF-8')

    for nid, score in sorted(scores.items()):
        rounded_score = round(score, NDIGITS)
        outfile.write("score({}): {}\n".format(nid, rounded_score))

    exit(0)
