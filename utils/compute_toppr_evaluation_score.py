#!/usr/bin/env python3

import os
import re
import sys
import csv
import tqdm
import math
import pathlib
import argparse
import subprocess

COMPARE_FILENAMES = {'looprank': 'enwiki.{algo}.f{scoring_function}.{title}.{maxloop}.2018-03-01.compare.toppr.txt',
                     'ssppr': 'enwiki.{algo}.a{alpha:.2f}.{title}.{maxloop}.2018-03-01.compare.toppr.txt',
                     'cheir': 'enwiki.{algo}.a{alpha:.2f}.{title}.{maxloop}.2018-03-01.compare.toppr.txt',
                     '2Drank': 'enwiki.{algo}.a{alpha:.2f}.{title}.{maxloop}.2018-03-01.compare.toppr.txt',
                     }
ALLOWED_ALGOS = list(COMPARE_FILENAMES.keys())

COMPARISON_FILE_HEADER = ('pos', 'title', 'page_id', 'score')
OUTPUT_FILENAME = 'enwiki.comparison.{algo}.{title}.{maxloop}.2018-03-01.toppr.txt'


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


def read_comparison_file(algo,
                         alpha,
                         scoring_function,
                         title,
                         maxloop,
                         wholenetwork,
                         comparison_dir):

    if algo != 'looprank' and wholenetwork:
        input_filename = (COMPARE_FILENAMES[algo]
                          .format(algo=algo,
                                  alpha=alpha,
                                  title=title,
                                  maxloop='wholenetwork'
                                  )
                          )
    else:
        input_filename = (COMPARE_FILENAMES[algo]
                          .format(algo=algo,
                                  alpha=alpha,
                                  title=title,
                                  maxloop=maxloop,
                                  scoring_function=scoring_function
                                  )
                          )

    input_file = comparison_dir/input_filename


    links = {}
    try:
        with input_file.open('r') as infp:
            reader = csv.reader(infp, delimiter='\t')

            # ['5', 'Bijbehara railway station', '11119524', '2.41667']
            for line in reader:
                data = dict()
                data['pos'] = int(line[0])
                data['title'] = line[1]
                data['score'] = float(line[3])

                page_id = int(line[2])

                links[page_id] = data
    except FileNotFoundError:
        print("File {} not found.".format(input_file), file=sys.stderr)

    return links


def compute_score(links, use_log=False):
    pos = 0
    score = 0.0
    title = ''
    try:
        pos = links[lid]['pos']
        title = links[lid]['title']
    except KeyError:
        pass

    if use_log:

      try:
        score = 1.0/(1+math.log(pos))
      except ValueError:
        score = 0.0

    else:

      try:
          score = 1.0/pos
      except ZeroDivisionError:
          score = 0.0

    return pos, score, title


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Compute comparison score between LR and SSPPR.')
    parser.add_argument('-t', '--toppr',
                        type=pathlib.Path,
                        required=True,
                        help='Top Indegree file.'
                        )
    parser.add_argument('--limit-toppr',
                        type=int,
                        default=1000,
                        help='Limit number of Top Indegree articles.'
                        )
    parser.add_argument('--limit-algo',
                        type=int,
                        default=math.inf,
                        help='Limit number of algorithm articles.'
                        )
    parser.add_argument('-a', '--algo',
                        type=str,
                        choices=ALLOWED_ALGOS,
                        metavar='ALGO',
                        default='looprank',
                        help=('Name of the  algorithm to use. '
                              'Choices: {{{}}}. '
                              '[default: looprank].'
                              ).format(', '.join(ALLOWED_ALGOS))
                        )
    parser.add_argument('--alpha',
                        type=float,
                        default=0.85,
                        help='Alpha PageRank damping factor '
                             '[default: 0.85].'
                        )
    parser.add_argument('-f', '--scoring-function',
                        type=str,
                        default='linear',
                        choices=['linear', 'square', 'cube', 'nlogn',
                                 'expe', 'exp10'],
                        help='LoopRank scoring function '
                             '[default: linear].'
                        )
    parser.add_argument('-i', '--input',
                        type=pathlib.Path,
                        help='File with page titles '
                             '[default: read from stdin].'
                        )
    parser.add_argument('-k', '--maxloop',
                        type=int,
                        default=4,
                        help='Max loop length [default: 4].'
                        )
    parser.add_argument('--log',
                        action='store_true',
                        help='Use 1/log(n) to compute the comparison score instead of 1/n.'
                        )
    parser.add_argument('--comparison-dir',
                        type=pathlib.Path,
                        default=pathlib.Path('.'),
                        help='File with page titles '
                             '[default: read from stdin].'
                        )
    parser.add_argument('-w', '--wholenetwork',
                        action='store_true',
                        help='Run PageRank, CheiRank, 2Drank '
                             'on the whole network.'
                        )

    args = parser.parse_args()
    comparison_dir = args.comparison_dir
    algo = args.algo

    print('* Read input. ', file=sys.stderr)
    infile = None
    if args.input:
        infile = args.input.open('r')
    else:
        infile = sys.stdin

    titles = [_.strip() for _ in infile.readlines()]

    # print('* Read the "top indegree" file: ', file=sys.stderr)
    toppr_file = args.toppr
    topprlen = count_file_lines(toppr_file)
    toppr = list()
    with tqdm.tqdm(total=topprlen) as pbar:
        with safe_path(toppr_file).open('r', encoding='utf-8') as topprfp:
            reader = csv.reader(topprfp, delimiter='\t')
            for l in reader:
                title = l[0].replace('_', ' ')
                pageid = int(l[1])

                toppr.append((title,pageid))
                pbar.update(1)

    limit_toppr = args.limit_toppr
    assert limit_toppr > 0, '--limit-toppr must be positive'
    # toppr_limit_set = set([el[0] for el in toppr[:limit_toppr]])
    toppr_limit_set = set([el[1] for el in toppr[:limit_toppr]])
    toppr_pos = dict([(el[1][0],el[0]+1) for el in enumerate(toppr[:limit_toppr])])

    limit_algo = args.limit_algo

    print('* Processing titles: ', file=sys.stderr)
    for title in titles:
        score = 0.0

        scores = dict()
        pos = dict()
        print('-'*80)
        print('    - {}'.format(title), file=sys.stderr)

        links_algo = read_comparison_file(algo=algo,
                                           alpha=args.alpha,
                                           scoring_function=args.scoring_function,
                                           title=title,
                                           maxloop=args.maxloop,
                                           wholenetwork=args.wholenetwork,
                                           comparison_dir=comparison_dir
                                           )

        links_set = set(links_algo.keys())
        for lid in links_set:
            pos_algo, score_algo, title_algo = compute_score(links_algo, use_log=args.log)

            # if pos_algo <= limit_algo and title_algo in toppr_limit_set:
            if pos_algo <= limit_algo and lid in toppr_limit_set:
                score += score_algo

                title_link = title_algo
                scores[title_link] = score_algo
                pos[title_link] = pos_algo

        function='linear'
        if args.log:
          function='log'

        outfile = sanitize(
            'enwiki.evaluate.{algo}.{title}.2018-03-01.scores.{function}.txt'
            .format(title=title.replace(' ', '_'),
                    algo=algo,
                    function=function
                    )
            )

        with open(outfile, 'w+') as outfp:
            writer = csv.writer(outfp, delimiter='\t')
            writer.writerow((score,))
            for link_title in scores:
                writer.writerow((scores[link_title],
                                 link_title,
                                 pos[link_title],
                                 toppr_pos[link_title]
                                 )
                                )

    exit(0)
