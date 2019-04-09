#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import csv
import glob
import tqdm
import pathlib
import argparse
import itertools
import subprocess


ALGOS = ('looprank', 'ssppr')
SCORES_FILENAMES = {'looprank': 'enwiki.{algo}.{title}.4.2018-03-01.scores.txt',
                    'ssppr': 'enwiki.{algo}.{title}.4.2018-03-01.txt',
                    }
ALLOWED_ALGOS = list(SCORES_FILENAMES.keys())
OUTPUT_FILENAME = 'enwiki.{algo}.{title}.2018-03-01.compare.txt'


# sanitize regex
sanre01 = re.compile(r'[\\/:&\*\?"<>\|\x01-\x1F\x7F]')
sanre02 = re.compile(r'^\(nul\|prn\|con\|lpt[0-9]\|com[0-9]\|aux\)\(\.\|$\)',
                     re.IGNORECASE)
sanre03 = re.compile(r'^\.*$')
sanre04 = re.compile(r'^$')

def sanitize(filename: str) -> str:
    res = sanre01.sub('', filename)
    res = sanre02.sub('', res)
    res = sanre03.sub('', res)
    res = sanre04.sub('', res)

    return res


# Processing non-UTF-8 Posix filenames using Python pathlib?
# https://stackoverflow.com/a/45724695/2377454
def safe_path(path: pathlib.Path) -> pathlib.Path:
    encoded_path = path.as_posix().encode('utf-8')
    return pathlib.Path(os.fsdecode(encoded_path))


# How to get line count cheaply in Python?
# https://stackoverflow.com/a/45334571/2377454
def count_file_lines(file_path: pathlib.Path) -> int:
    """
    Counts the number of lines in a file using wc utility.
    :param file_path: path to file
    :return: int, no of lines
    """

    num = subprocess.check_output(
        ['wc', '-l', safe_path(file_path).as_posix()])
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
    parser.add_argument('--links-filename',
                        help='Links file name (default: derive from title)'
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

    # print('* Read input. ', file=sys.stderr)
    infile = None
    if args.input:
        infile = safe_path(args.input).open('r', encoding='utf-8')
    else:
        infile = sys.stdin

    titles = [_.strip()
              for _ in infile.readlines()
              ]

    # print('* Read the "snapshot" file: ', file=sys.stderr)
    snapshot_file = args.snapshot
    snaplen = count_file_lines(snapshot_file)
    snapshot = dict()
    with tqdm.tqdm(total=snaplen) as pbar:
        with safe_path(snapshot_file).open('r', encoding='utf-8') as snapfp:
            reader = csv.reader(snapfp, delimiter='\t')
            for l in reader:
                snapshot[int(l[0])] = l[1]
                pbar.update(1)

    # print('* Processing titles: ', file=sys.stderr)
    links_dir = args.links_dir
    scores_dir = args.scores_dir
    for title in titles:
        # print('-'*80)
        # print('    - {}'.format(title), file=sys.stderr)

        if args.links_filename is None:
            links_filename = sanitize('enwiki.comparison.{title}.seealso.txt'
                              .format(title=title))
        else:
            links_filename = sanitize(args.links_filename)


        for alinkfile in (os.path.basename(x)
                          for x in glob.glob(links_dir.as_posix() + '/*')):
            if sanitize(alinkfile) == links_filename:
                links_file = links_dir/pathlib.Path(alinkfile)
                break

        with safe_path(links_file).open('r', encoding='utf-8') as linkfp:
            reader = csv.reader(linkfp, delimiter='\t')
            next(reader)

            links_ids = set()
            for line in reader:
                lid = int(line[1])
                links_ids.add(lid)

        for  lid in links_ids:
            link_title = snapshot[lid]
            # print('        > {}'.format(link_title), file=sys.stderr)

        for algo in ALGOS:
            # print('      * Read score ({}) file'.format(algo),
            #      file=sys.stderr)
            scores_filename = sanitize(SCORES_FILENAMES[algo].format(algo=algo,
                                       title=title.replace(' ', '_'))
                                       )

            for ascorefile in (os.path.basename(x)
                            for x in glob.glob(scores_dir.as_posix() + '/*')):
                if sanitize(ascorefile) == scores_filename:
                    scores_file = scores_dir/pathlib.Path(ascorefile)
                    break

            all_outlines = []
            scoreslen = count_file_lines(scores_file)


            with safe_path(scores_file).open('r', encoding='UTF-8') \
                    as scoresfp:
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

            # print('      * Print results for algo {}'.format(algo),
            #       file=sys.stderr)

            output_dir = args.output_dir
            output_filename = sanitize(OUTPUT_FILENAME.format(algo=algo,
                                       title=title.replace(' ', '_'))
                                       )
            output_file = output_dir/output_filename

            with safe_path(output_file).open('w+', encoding='UTF-8') as outfp:
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
