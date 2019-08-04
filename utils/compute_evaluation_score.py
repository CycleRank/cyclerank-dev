#!/usr/bin/env python3

import re
import sys
import csv
import math
import pathlib
import argparse

COMPARE_FILENAMES = {'looprank': 'enwiki.{algo}.f{scoring_function}.{title}.{maxloop}.2018-03-01.compare.seealso.txt',
                     'ssppr': 'enwiki.{algo}.a{alpha}.{title}.{maxloop}.2018-03-01.compare.seealso.txt',
                     'cheir': 'enwiki.{algo}.a{alpha}.{title}.{maxloop}.2018-03-01.compare.seealso.txt',
                     '2Drank': 'enwiki.{algo}.a{alpha}.{title}.{maxloop}.2018-03-01.compare.seealso.txt',
                     }
ALLOWED_ALGOS = list(COMPARE_FILENAMES.keys())

COMPARISON_FILE_HEADER = ('pos', 'title', 'page_id', 'score')
OUTPUT_FILENAME = 'enwiki.{algo}.{title}.{maxloop}.2018-03-01.compare.txt'


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

    return score, title


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Compute comparison score between LR and SSPPR.')
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

    print('* Processing titles: ', file=sys.stderr)
    for title in titles:
        score = 0.0

        scores = dict()
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
            score_algo, title_algo = compute_score(links_algo, use_log=args.log)

            # import ipdb; ipdb.set_trace()
            score += score_algo

            title_link = title_algo
            scores[title_link] = score_algo

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
                writer.writerow((scores[link_title], link_title))

    exit(0)
