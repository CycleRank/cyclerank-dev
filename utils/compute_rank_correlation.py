#!/usr/bin/env python3

import re
import sys
import csv
import math
import pathlib
import argparse
from operator import itemgetter
from scipy.stats import rankdata, kendalltau

COMPARE_FILENAMES = {'looprank': 'enwiki.{algo}.f{scoring_function}.{title}.{maxloop}.2018-03-01.compare.clickstream.txt',
                     'ssppr': 'enwiki.{algo}.a{alpha:.2f}.{title}.{maxloop}.2018-03-01.compare.clickstream.txt',
                     'cheir': 'enwiki.{algo}.a{alpha:.2f}.{title}.{maxloop}.2018-03-01.compare.clickstream.txt',
                     '2Drank': 'enwiki.{algo}.a{alpha:.2f}.{title}.{maxloop}.2018-03-01.compare.clickstream.txt',
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


def read_links_file(title,
                    links_dir):

    links_filename = ('enwiki.comparison.{title}.clickstream.txt'
                      .format(title=title))

    links_file = links_dir/links_filename

    links = {}
    try:
        with links_file.open('r') as infp:
            reader = csv.reader(infp, delimiter='\t')

            # skip header
            next(reader)

            # link_title  link_id click_count
            # Mughal-e-Azam 317154  147

            for line in reader:
                data = dict()
                links_id = int(line[1])

                data['title'] = line[0]
                data['count'] = int(line[2])

                links[links_id] = data

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
    parser.add_argument('--links-dir',
                        required=True,
                        type=pathlib.Path,
                        default=pathlib.Path('.'),
                        help='Directory with links files'
                        )
    parser.add_argument('--comparison-dir',
                        required=True,
                        type=pathlib.Path,
                        default=pathlib.Path('.'),
                        help='Directory with comparison files'
                        )
    parser.add_argument('-w', '--wholenetwork',
                        action='store_true',
                        help='Run PageRank, CheiRank, 2Drank '
                             'on the whole network.'
                        )

    args = parser.parse_args()
    comparison_dir = args.comparison_dir
    links_dir = args.links_dir
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

        links_ref = read_links_file(title=title, links_dir=links_dir)

        assert all(key in links_ref for key in links_algo), \
                'Error: unexpected key in the comparison results'

        for key in links_ref:
          if key not in links_algo:
            links_algo[key] = {'pos': -1,
                               'title': links_ref[key]['title'],
                               'score': 0,
                               }

        rank_algo = sorted([(key, links_algo[key]['score'])
                            for key in links_algo],
                            key=itemgetter(1),
                            reverse=True)

        rank_ref = sorted([(key, links_ref[key]['count'])
                           for key in links_ref],
                           key=itemgetter(1),
                           reverse=True)

        stdrank_algo = rankdata([-el[1] for el
                                          in sorted(rank_algo,key=itemgetter(0))
                                          ])
        cmprank_algo = list(zip([el[0] for el
                                 in sorted(rank_algo,key=itemgetter(0))],
                                stdrank_algo
                                ))


        stdrank_ref =rankdata([-el[1] for el
                               in sorted(rank_ref,key=itemgetter(0))
                               ])
        cmprank_ref = list(zip([el[0] for el
                                in sorted(rank_ref,key=itemgetter(0))],
                               stdrank_ref
                               ))

        ktau = kendalltau(stdrank_ref, stdrank_algo)

        outfile = sanitize(
            'enwiki.evaluate.{algo}.{title}.2018-03-01.clickstream.txt'
            .format(title=title.replace(' ', '_'),algo=algo)
            )

        if not math.isnan(ktau.correlation):
          with open(outfile, 'w+') as outfp:
              writer = csv.writer(outfp, delimiter='\t')
              writer.writerow((ktau.correlation, ktau.pvalue))

    exit(0)
