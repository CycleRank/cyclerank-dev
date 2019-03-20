#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
import csv
import tqdm
import pathlib
import argparse
import itertools
import subprocess


ALGOS = ('looprank', 'ssppr')
SCORES_FILENAMES = {'looprank': 'enwiki.{algo}.{title}.4.2018-03-01.scores.txt',
                    'ssppr': 'enwiki.{algo}.{title}.4.2018-03-01.txt',
                    }
OUTPUT_FILENAME = 'enwiki.{algo}.{title}.2018-03-01.compare_lr-pr.txt'


# How to get line count cheaply in Python?
# https://stackoverflow.com/a/45334571/2377454
def count_file_lines(file_path):
    """
    Counts the number of lines in a file using wc utility.
    :param file_path: path to file
    :return: int, no of lines
    """
    num = subprocess.check_output(['wc', '-l', file_path])
    num = num.decode('utf-8').strip().split(' ')
    return int(num[0])


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
        description='Compute "See also" position from LR and SSPPR.')
    parser.add_argument('-i', '--input',
                        type=pathlib.Path,
                        help='File with page titles '
                             '[default: read from stdin].'
                        )
    parser.add_argument('-l', '--links-dir',
                        type=pathlib.Path,
                        default=pathlib.Path('.'),
                        help='Directory with the link files [default: .]'
                        )
    parser.add_argument('--output-dir',
                        type=pathlib.Path,
                        default=pathlib.Path('.'),
                        help='Directory where to put output files [default: .]'
                        )
    parser.add_argument('--scores-dir',
                        type=pathlib.Path,
                        default=pathlib.Path('.'),
                        help='Directory with the scores files [default: .]'
                        )
    parser.add_argument('-s', '--snapshot',
                        type=pathlib.Path,
                        required=True,
                        help='Wikipedia snapshot with the id-title mapping.'
                        )

    args = parser.parse_args()

    print('* Read input. ', file=sys.stderr)
    infile = None
    if args.input:
        infile = args.input.open('r', encoding='UTF-8')
    else:
        infile = sys.stdin

    titles = [_.strip()
              for _ in infile.readlines()
              ]

    print('* Read the "snapshot" file: ', file=sys.stderr)
    snapshot_file = args.snapshot
    snaplen = count_file_lines(snapshot_file)
    snapshot = dict()
    with tqdm.tqdm(total=snaplen) as pbar:
        with snapshot_file.open('r', encoding='UTF-8') as snapfp:
            reader = csv.reader(snapfp, delimiter='\t')
            for l in reader:
                snapshot[int(l[0])] = l[1]
                pbar.update(1)

    print('* Processing titles: ', file=sys.stderr)
    links_dir = args.links_dir
    scores_dir = args.scores_dir
    for title in titles:
        print('-'*80)
        print('    - {}'.format(title.decode()), file=sys.stderr)


        links_filename = ('enwiki.comparison.{title}.seealso.txt'
                          .format(title=title.decode()))
        links_file = links_dir/links_filename

        with links_file.open('rb') as linkfp:
            reader = csv.reader(linkfp, delimiter=b'\t')
            next(reader)
            links_ids = dict((int(l[1].decode('utf-8')),
                              l[0].decode('utf-8'))
                             for l in reader
                             )

        for  lid in links_ids:
            link_title = snapshot[lid]
            print('        > {}'.format(link_title), file=sys.stderr)

        for algo in ALGOS:
            print('      * Read score ({}) file'.format(algo),
                  file=sys.stderr)
            scores_filename = (SCORES_FILENAMES[algo].format(algo=algo,
                               title=title.replace(' ', '_'))
                               )
            scores_file = scores_dir/scores_filename

            all_outlines = []
            scoreslen = count_file_lines(scores_file)
            with scores_file.open('r', encoding='UTF-8') as scoresfp:
                with tqdm.tqdm(total=scoreslen, leave=False) as pbar:
                    for line in scoresfp:
                        page_id, score = process_line(line)

                        if page_id:
                            all_outlines.append((page_id, score))

                        pbar.update(1)


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

            print('      * Print results for algo {}'.format(algo),
                  file=sys.stderr)

            output_dir = args.output_dir
            output_filename = (OUTPUT_FILENAME.format(algo=algo,
                               title=title.replace(' ', '_'))
                               )
            output_file = output_dir/output_filename

            with output_file.open('w+', encoding='UTF-8') as outfp:
                outwriter = csv.writer(outfp, delimiter='\t')
                for lid in link_positions:
                    link_title = snapshot[lid]
                    link_pos = link_positions[lid]
                    link_score = scores[lid]

                    # 'pos title lid score'
                    outwriter.writerow((link_pos,
                                        link_title,
                                        lid,
                                        repr(link_score)
                                        )
                                       )

    exit(0)
