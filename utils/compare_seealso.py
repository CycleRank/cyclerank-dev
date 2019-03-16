#!/usr/bin/env python3

import sys
import csv
import re
import argparse
import pathlib
import itertools

# Regex:
#  score(<pageid>):<spaces><score>
#
# where:
#   - <pageid> is an integer number
#   - <score> is a real number that can be written using the scientific
#     notation
REGEX_SCORE = r'score\(([0-9]+)\):\s+([0-9]+\.?[0-9]*e?-?[0-9]*)'
regex_score = re.compile(REGEX_SCORE)


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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Map wikipedia page ids to page titles.')

    parser.add_argument('-i', '--input',
                        type=pathlib.Path,
                        help='File with scores [default: read from stdin].'
                        )
    parser.add_argument('-l', '--links',
                        type=pathlib.Path,
                        help='File with link.'
                        )
    parser.add_argument('-o', '--output',
                        type=pathlib.Path,
                        help='Sort results in desceding order. If --sort is '
                             'not given this option is effectively ignored.'
                        )
    parser.add_argument('-s', '--snapshot',
                        type=pathlib.Path,
                        required=True,
                        help='Wikipedia snapshot with the id-title mapping.'
                        )

    args = parser.parse_args()

    snapshot_file = args.snapshot
    with snapshot_file.open('r') as snapfp:
        reader = csv.reader(snapfp, delimiter='\t')
        snapshot = dict((int(l[0]), l[1]) for l in reader)

    links_file = args.links
    with links_file.open('r') as linkfp:
        reader = csv.reader(linkfp, delimiter='\t')
        next(reader)
        links_ids = dict((int(l[1]), l[0]) for l in reader)

    all_outlines = []
    infile = None
    if args.input:
        infile = open(args.input, 'r')
    else:
        infile = sys.stdin

    try:
        for line in infile:
            page_id, score = process_line(line)

            if page_id:
                all_outlines.append((page_id, score))

    except IOError as err:
        if err.errno == errno.EPIPE:
            pass

    sorted_lines = sorted(all_outlines,
                          key=lambda tup: tup[1],
                          reverse=True
                          )
    scores = dict(sorted_lines)

    link_positions = dict()
    for lid in links_ids:
        for pos, item in enumerate(sorted_lines):
            if lid == item[0]:
                link_positions[lid] = pos + 1
                break

    outline = '{pos}\t{title}\t{lid}\t{score}\n'
    try:
        for lid in link_positions:
            title = snapshot[lid]
            pos = link_positions[lid]
            score = scores[lid]
            sys.stdout.write(outline.format(pos=pos,
                                            title=title,
                                            lid=lid,
                                            score=repr(score)
                                            )
                             )

    except IOError as err:
        if err.errno == errno.EPIPE:
            pass

    exit(0)
