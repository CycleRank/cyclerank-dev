#!/usr/bin/env python3

import os
import re
import sys
import csv
import math
import argparse
import pathlib
import itertools

# Score regex
#
#  score(<pageid>):<spaces><score>
#
# where:
#   - <pageid> is an integer number
#   - <score> is a real number that can be written using the scientific
#     notation
REGEX_SCORE = r'score\(([0-9]+)\):\s+([0-9]+\.?[0-9]*e?-?[0-9]*)'
regex_score = re.compile(REGEX_SCORE)


# Name regex
#
# example name:
# enwiki.cheir.1999_Bridge_Creek–Moore_tornado.4.2018-03-01.txt
#
REGEX_NAME = r'([a-z]{2}wiki)\.cheir\.(.+)\.(.+)\.(\d{4}-\d{2}-\d{2})\.txt'
regex_name = re.compile(REGEX_NAME)



def process_line(line):
    match = regex_score.match(line)

    title = None
    score = None
    if match:
        pageid = int(match.group(1))
        score = float(match.group(2))
    else:
        print('Error: could not process line: {}'.format(line),
              file=sys.stderr)

    # if match fails this is (None, None)
    return pageid, score


def sort2d(x):
    pageid = x[0]
    positions = x[1]

    cheirpos = positions[0]
    sspprpos = positions[1]

    lowpos = -max(cheirpos, sspprpos)
    sumpos = -(cheirpos+sspprpos)

    return (lowpos, sumpos, -pageid)


def rank(algoscores):
    res = {}
    pos = 0
    score = 1.0
    for k in sorted(algoscores, key=algoscores.get, reverse=True):
        elscore = algoscores[k]

        if elscore < score:
            pos = pos + 1
            score = elscore

        res[k] = {'score': elscore,
                  'pos': pos
                  }

    return res


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Combine Personalized PageRank and CheiRank to obtain 2Drank.')

    parser.add_argument('-c', '--cheirank',
                        type=pathlib.Path,
                        required=True,
                        help='File with scores from CheiRank.'
                        )
    parser.add_argument('-o', '--output-dir',
                        type=pathlib.Path,
                        default=pathlib.Path('.'),
                        help='Output directory.'
                        )
    parser.add_argument('-s', '--ssppr',
                        type=pathlib.Path,
                        required=True,
                        help='File with scores from PageRank.'
                        )

    args = parser.parse_args()

    cheir_filename = os.path.basename(args.cheirank.as_posix())
    match = regex_name.match(cheir_filename)

    proj = match.group(1)
    title = match.group(2)
    maxloop = match.group(3)
    date = match.group(4)

    # {proj}.2Drank.{title}.{maxloop}.{date}.txt
    output_filename = ('{0}.2Drank.{1}.{2}.{3}.txt'
                       .format(proj, title, maxloop, date)
                       )

    ssppr_file = args.ssppr
    cheir_file = args.cheirank

    cheir = {}
    ssppr = {}

    with cheir_file.open('r') as incheir:
        for line in incheir:
            pageid, score = process_line(line)
            cheir[pageid] = score

    with ssppr_file.open('r') as inssppr:
        for line in inssppr:
            pageid, score = process_line(line)
            ssppr[pageid] = score

    ids = set(cheir.keys()).intersection(set(ssppr.keys()))

    cheirsort = rank(cheir)
    del(cheir)

    sspprsort = rank(ssppr)
    del(ssppr)

    scores = {}
    for idx in ids:
        cheirdata = cheirsort[idx]
        sspprdata = sspprsort[idx]

        scores[idx] = (cheirsort[idx]['pos'], sspprsort[idx]['pos'])
    del cheirsort
    del sspprsort


    rank2d = sorted(scores.items(), key=sort2d, reverse=True)

    output_dir = args.output_dir
    output_file = output_dir/output_filename
    with output_file.open('w+') as outfp:
        for pageid, positions in rank2d:
            # cheirpos = positions[0]
            # sspprpos = positions[1]

            # score = math.sqrt(cheirpos*cheirpos+sspprpos*sspprpos)
            # outfp.write('score({}):\t{}\n'.format(pageid, score))
            outfp.write('{}\n'.format(pageid))

    exit(0)
