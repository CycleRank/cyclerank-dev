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

REGEX_ID = r'([0-9]+)'
regex_id = re.compile(REGEX_ID)


# output templates
OUTLINE_SCORE = 'score({title}):\t{score}\n'
OUTLINE_NOSCORE = '{title}\n'


def process_line(line):
    match_score = regex_score.match(line)
    match_id = regex_id.match(line)

    title = None
    score = None
    if match_score:
        pageid = int(match_score.group(1))
        score = float(match_score.group(2))
        title = snapshot[pageid]
    elif match_id:
        pageid = int(match_id.group(1))
        title = snapshot[pageid]
    else:
        print('Error: could not process line: {}'.format(line),
              file=sys.stderr)

    # if match fails this is (None, None)
    return title, score


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Map wikipedia page ids to page titles.')

    parser.add_argument('-i', '--input',
                        type=pathlib.Path,
                        help='File with scores [default: read from stdin].'
                        )
    parser.add_argument('-s', '--snapshot',
                        type=pathlib.Path,
                        required=True,
                        help='Wikipedia snapshot with the id-title mapping.'
                        )
    parser.add_argument('--sort',
                        choices=['score','title'],
                        help='Sort results in ascending order with respect '
                             'to the given column. Choose between '
                             '{score, title}.'
                        )
    parser.add_argument('-r', '--reverse',
                        action='store_true',
                        help='Sort results in desceding order. If --sort is '
                             'not given this option is effectively ignored.'
                        )


    args = parser.parse_args()

    snapshotname = args.snapshot
    with snapshotname.open('r') as snapshotfile:
        reader = csv.reader(snapshotfile, delimiter='\t')
        snapshot = dict((int(l[0]), l[1]) for l in reader)

    all_outlines = []
    infile = None
    if args.input:
        infile = open(args.input, 'r')
    else:
        infile = sys.stdin

    try:
        for line in infile:
            title, score = process_line(line)

            if title:
                if score and args.sort:
                    all_outlines.append((title, score))
                else:
                    if score:
                        sys.stdout.write(OUTLINE_SCORE.format(
                            title=title, score=repr(score)))
                    else:
                        sys.stdout.write(OUTLINE_NOSCORE.format(title=title))

    except IOError as err:
        if err.errno == errno.EPIPE:
            pass

    if all_outlines and args.sort:
        sortkey = args.sort
        if sortkey == 'score':
            sorted_lines = sorted(all_outlines,
                                  key=lambda tup: tup[1],
                                  reverse=args.reverse
                                  )
        else:
            # sortkey == 'title'
            sorted_lines = sorted(all_outlines,
                                  key=lambda tup: tup[0],
                                  reverse=args.reverse
                                  )


        try:
            for title, score in sorted_lines:
                if title:
                    sys.stdout.write(OUTLINE_SCORE.format(
                        title=title, score=repr(score)))
        except IOError as err:
            if err.errno == errno.EPIPE:
                pass

    exit(0)
