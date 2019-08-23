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

# Name regex
#
# example name:
# enwiki.cheir.1999_Bridge_Creek–Moore_tornado.4.2018-03-01.txt
#
REGEX_NAME = (r'([a-z]{2}wiki)\.(cheir|ssppr|cheir|2Drank)' + \
              r'\.(.+)\.(.+)\.(\d{4}-\d{2}-\d{2})\.txt')
regex_name = re.compile(REGEX_NAME)

SCORES_FILENAMES = {
'looprank': 'enwiki.{algo}.f{scoring_function}.{title}.{maxloop}.2018-03-01.scores.txt',
'ssppr': 'enwiki.{algo}.a{alpha:.2f}.{title}.{maxloop}.2018-03-01.txt',
'cheir': 'enwiki.{algo}.a{alpha:.2f}.{title}.{maxloop}.2018-03-01.txt',
'2Drank': 'enwiki.{algo}.a{alpha:.2f}.{title}.{maxloop}.2018-03-01.txt',
}
ALLOWED_ALGOS = list(SCORES_FILENAMES.keys())
OUTPUT_FILENAMES = {
'looprank': 'enwiki.{algo}.f{scoring_function}.{title}.{maxloop}.2018-03-01.compare.{method}.txt',
'ssppr': 'enwiki.{algo}.a{alpha:.2f}.{title}.{maxloop}.2018-03-01.compare.{method}.txt',
'cheir': 'enwiki.{algo}.a{alpha:.2f}.{title}.{maxloop}.2018-03-01.compare.{method}.txt',
'2Drank': 'enwiki.{algo}.a{alpha:.2f}.{title}.{maxloop}.2018-03-01.compare.{method}.txt',
}

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
        description='Compute "See also" position from LR and SSPPR/CHEIR.')
    parser.add_argument('-a', '--algo',
                        choices=ALLOWED_ALGOS,
                        metavar='ALGO',
                        nargs='+',
                        type=str,
                        default=['looprank', 'ssppr'],
                        help=('Name of the  algorithms to use. '
                              'Choices: {{{}}}. '
                              '[default: [looprank, ssppr]].'
                              ).format(', '.join(ALLOWED_ALGOS))
                        )
    parser.add_argument('--alpha',
                        type=float,
                        default=0.85,
                        help='Damping factor (alpha) for the PageRank '
                             'algorithm [default: 0.85].'
                        )
    parser.add_argument('--clickstream',
                        action='store_true',
                        help='Use clickstream data instead of see also.'
                        )
    parser.add_argument('-f', '--scoring-function',
                        type=str,
                        default='linear',
                        help='Scoring function used for LoopRank '
                             'algorithm [default: "linear"].'
                        )
    parser.add_argument('-i', '--input',
                        type=pathlib.Path,
                        help='File with page titles or page indexes '
                             '[default: read from stdin].'
                        )
    parser.add_argument('--index',
                        action='store_true',
                        help='Use page indexes instead of titles.'
                        )
    parser.add_argument('-k', '--maxloop',
                        type=int,
                        default=4,
                        help='Maxloop prefix in the file [default: 4].'
                        )
    parser.add_argument('-l', '--links-dir',
                        type=pathlib.Path,
                        default=pathlib.Path('.'),
                        help='Directory with the link files [default: .]'
                        )
    parser.add_argument('--links-filename',
                        help='Links file name (default: derive from title)'
                        )
    parser.add_argument('-o', '--output-dir',
                        type=pathlib.Path,
                        default=pathlib.Path('.'),
                        help='Directory where to put output files [default: .]'
                        )
    parser.add_argument('--scores-dir',
                        type=pathlib.Path,
                        default=pathlib.Path('.'),
                        help='Directory with the scores files [default: .]'
                        )
    parser.add_argument('-w', '--wholenetwork',
                        action='store_true',
                        help='Calculate SSPPR, Cheir, and 2Drank on the '
                             'wholenetwork.'
                        )
    parser.add_argument('-s', '--snapshot',
                        type=pathlib.Path,
                        required=True,
                        help='Wikipedia snapshot with the id-title mapping.'
                        )

    args = parser.parse_args()
    maxloop = args.maxloop
    alpha = args.alpha
    scoring_function = args.scoring_function

    # print('* Read input. ', file=sys.stderr)
    infile = None
    if args.input:
        infile = safe_path(args.input).open('r', encoding='utf-8')
    else:
        infile = sys.stdin

    titles = [_.strip()
              for _ in infile.readlines()
              ]
    if '\t' in titles[0]:
        if args.index:
            titles = [line.split('\t')[1] for line in titles]
        else:
            titles = [line.split('\t')[0] for line in titles]

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
        links_filename = None
        # print('-'*80)
        # print('    - {}'.format(title), file=sys.stderr)
        if args.links_filename is None:
            if args.clickstream:
                links_filename = sanitize('enwiki.comparison.{title}.clickstream.txt'
                                          .format(title=title))
            else:
                links_filename = sanitize('enwiki.comparison.{title}.seealso.txt'
                                          .format(title=title))
        else:
            links_filename = sanitize(args.links_filename)

        # print('        -> links_filename: {}'.format(links_filename),
        #       file=sys.stderr)

        for alinkfile in (os.path.basename(x)
                          for x in glob.glob(links_dir.as_posix() + '/*')):
            if sanitize(alinkfile) == links_filename:
                links_file = links_dir/pathlib.Path(alinkfile)
                break

        if not links_file:
            raise ValueError('Links file not found.')

        with safe_path(links_file).open('r', encoding='utf-8') as linkfp:
            reader = csv.reader(linkfp, delimiter='\t')

            # skip header
            next(reader)

            links_ids = set()
            for line in reader:
                lid = int(line[1])
                links_ids.add(lid)

        for  lid in links_ids:
            link_title = snapshot[lid]
            # print('        > {}'.format(link_title), file=sys.stderr)

        for algo in args.algo:
            scores_filename = None
            scores_file = None
            # print('      * Read score ({}) file'.format(algo),
            #       file=sys.stderr)

            if algo != 'looprank':
                scores_filename = sanitize(SCORES_FILENAMES[algo].format(
                    alpha=alpha,
                    algo=algo,
                    title=title.replace(' ', '_'),
                    maxloop=maxloop
                    )
                )
                if args.wholenetwork:
                    scores_filename = sanitize(SCORES_FILENAMES[algo].format(
                        alpha=alpha,
                        algo=algo,
                        title=title.replace(' ', '_'),
                        maxloop='wholenetwork'
                        )
                    )
            else:
                scores_filename = sanitize(SCORES_FILENAMES[algo].format(
                    algo=algo,
                    title=title.replace(' ', '_'),
                    maxloop=maxloop,
                    scoring_function=scoring_function
                    )
                )

            print('        -> scores_filename: {}'.format(scores_filename),
                   file=sys.stderr)

            for ascorefile in (os.path.basename(x)
                            for x in glob.glob(scores_dir.as_posix() + '/*')):
                if sanitize(ascorefile) == scores_filename:
                    scores_file = scores_dir/pathlib.Path(ascorefile)
                    break

            if not scores_file:
                raise ValueError('Score file not found.')

            # print('        -> scores_file: {}'.format(scores_file),
            #       file=sys.stderr)

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
            method = 'seealso'
            if args.clickstream:
                method = 'clickstream'
            if algo != 'looprank':
                output_filename = sanitize(OUTPUT_FILENAMES[algo].format(
                    algo=algo,
                    alpha=alpha,
                    title=title.replace(' ', '_'),
                    maxloop=maxloop,
                    method=method
                    )
                )
                if  args.wholenetwork:
                    output_filename = sanitize(OUTPUT_FILENAMES[algo].format(
                        algo=algo,
                        alpha=alpha,
                        title=title.replace(' ', '_'),
                        maxloop='wholenetwork',
                        method=method
                        )
                    )
            else:
                output_filename = sanitize(OUTPUT_FILENAMES[algo].format(
                    algo=algo,
                    title=title.replace(' ', '_'),
                    maxloop=maxloop,
                    scoring_function=scoring_function,
                    method=method
                    )
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
