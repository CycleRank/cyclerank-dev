#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import csv
import re
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


SCORING_FUNCTIONS = {
'linear': linear_score,
'square': square_score,
}


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
    with infile.open('r', encoding='UTF-8') as infp:
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
        outfile = output.open('w+', encoding='UTF-8')

    for nid, score in sorted(scores.items()):
        rounded_score = round(score, NDIGITS)
        outfile.write("score({}): {}\n".format(nid, rounded_score))

    exit(0)
