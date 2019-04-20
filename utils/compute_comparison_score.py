#!/usr/bin/env python3

import re
import sys
import csv
import pathlib
import argparse

COMPARE_FILENAMES = {'looprank': 'enwiki.{algo}.{title}.{maxloop}.2018-03-01.compare.txt',
                     'ssppr': 'enwiki.{algo}.{title}.{maxloop}.2018-03-01.compare.txt',
                     'cheir': 'enwiki.{algo}.{title}.{maxloop}.2018-03-01.compare.txt',
                     '2Drank': 'enwiki.{algo}.{title}.{maxloop}.2018-03-01.compare.txt',
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
                         title,
                         maxloop,
                         wholenetwork,
                         comparison_dir):

    if algo != 'looprank' and wholenetwork:
        input_filename = (COMPARE_FILENAMES[algo]
                          .format(algo=algo,
                                  title=title,
                                  maxloop='wholenetwork'
                                  )
                          )
    else:
        input_filename = (COMPARE_FILENAMES[algo]
                          .format(algo=algo,
                                  title=title,
                                  maxloop=maxloop
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


def compute_score(links):
    pos = 0
    score = 0.0
    title = ''
    try:
        pos = links[lid]['pos']
        title = links[lid]['title']
    except KeyError:
        pass

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
                        nargs=2,
                        choices=ALLOWED_ALGOS,
                        metavar='ALGO',
                        dest='algos',
                        default=['looprank', 'ssppr'],
                        help=('Name of the  algorithms to use. '
                              'Choices: {{{}}}. '
                              '[default: [looprank, ssppr]].'
                              ).format(', '.join(ALLOWED_ALGOS))
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

        algo1 = args.algos[0]
        algo2 = args.algos[1]

        links_algo1 = read_comparison_file(algo=algo1,
                                           title=title,
                                           maxloop=args.maxloop,
                                           wholenetwork=args.wholenetwork,
                                           comparison_dir=comparison_dir
                                           )

        links_algo2 = read_comparison_file(algo=algo2,
                                           title=title,
                                           maxloop=args.maxloop,
                                           wholenetwork=args.wholenetwork,
                                           comparison_dir=comparison_dir
                                           )

        links_set = set(links_algo1.keys()).union(set(links_algo2.keys()))
        for lid in links_set:
            score_algo1, title_algo1 = compute_score(links_algo1)
            score_algo2, title_algo2 = compute_score(links_algo2)

            # import ipdb; ipdb.set_trace()

            score_link = score_algo1 - score_algo2
            score += score_link

            title_link = title_algo1 if title_algo1 else title_algo2
            scores[title_link] = score_link

        outfile = sanitize(
            'enwiki.compare.{algo1}.{algo2}.{title}.2018-03-01.scores.txt'
            .format(title=title.replace(' ', '_'),
                    algo1=algo1,
                    algo2=algo2
                    )
            )

        with open(outfile, 'w+') as outfp:
            writer = csv.writer(outfp, delimiter='\t')
            writer.writerow((score,))
            for link_title in scores:
                writer.writerow((scores[link_title], link_title))

    exit(0)
