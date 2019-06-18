#!/usr/bin/env python3

import re
import sys
import csv
import errno
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
OUTLINE = '{title}\t{id_}\n'


def process_line(line):
    match_score = regex_score.match(line)
    match_id = regex_id.match(line)

    title = None
    score = None
    if match_score:
        pageid = int(match_score.group(1))
        score = float(match_score.group(2))
        title = id2title.get(pageid, None)
    elif match_id:
        pageid = int(match_id.group(1))
        title = title2id.get(pageid, None)
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
    id2title = {}
    title2id = {}
    with snapshotname.open('r') as snapshotfile:
        reader = csv.reader(snapshotfile, delimiter='\t')
        for l in reader:
            id_ = int(l[0])
            title = l[1]
            id2title[id_] = title
            title2id[title] = id_

    all_outlines = []
    infile = None
    if args.input:
        infile = args.input.open('r')
    else:
        infile = sys.stdin

    try:
        for line in infile:
            title, score = process_line(line)

            if title is not None:
                if score is not None and args.sort:
                    all_outlines.append((title, score))
                else:
                    sys.stdout.write(OUTLINE.format(
                        title=title, id_=title2id[title]))


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
                if title is not None:
                    sys.stdout.write(OUTLINE.format(
                        title=title, id_=title2id[title]))
        except IOError as err:
            if err.errno == errno.EPIPE:
                pass

    exit(0)
