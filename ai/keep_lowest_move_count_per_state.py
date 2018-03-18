#!/usr/bin/env python3

import logging
import os
import subprocess
import sys

'''
100k
====
             precision    recall  f1-score   support
        1.0       1.00      1.00      1.00     19877
        2.0       1.00      1.00      1.00      7595
        3.0       1.00      1.00      1.00      5747
        4.0       0.95      0.98      0.97      4038
        5.0       0.81      0.81      0.81      2860
        6.0       0.62      0.61      0.62      2645
        7.0       0.49      0.49      0.49      2944
        8.0       0.42      0.42      0.42      3020
        9.0       0.38      0.39      0.38      2820
       10.0       0.32      0.32      0.32      2537
       11.0       0.27      0.26      0.26      2170
       12.0       0.23      0.22      0.23      1848
       13.0       0.24      0.24      0.24      1564
       14.0       0.19      0.20      0.20      1242
       15.0       0.18      0.19      0.18      1107
       16.0       0.17      0.17      0.17       947
       17.0       0.16      0.15      0.16       815
       18.0       0.15      0.14      0.15       700
avg / total       0.74      0.74      0.74     64476


600k
====
             precision    recall  f1-score   support
        1.0       1.00      1.00      1.00    126197
        2.0       1.00      1.00      1.00     47301
        3.0       1.00      1.00      1.00     35491
        4.0       0.99      1.00      1.00     25483
        5.0       0.96      0.97      0.96     16663
        6.0       0.87      0.85      0.86     11601
        7.0       0.72      0.72      0.72      8829
        8.0       0.57      0.56      0.57      6826
        9.0       0.47      0.48      0.48      5606
       10.0       0.40      0.41      0.40      4562
       11.0       0.35      0.34      0.34      3764
       12.0       0.29      0.30      0.30      3005
       13.0       0.25      0.25      0.25      2483
       14.0       0.24      0.24      0.24      2027
       15.0       0.21      0.20      0.20      1695
       16.0       0.20      0.19      0.19      1399
       17.0       0.17      0.17      0.17      1162
       18.0       0.17      0.16      0.17       984
avg / total       0.92      0.92      0.92    305078


2 million
=========
             precision    recall  f1-score   support
        1.0       1.00      1.00      1.00    430449
        2.0       1.00      1.00      1.00    161473
        3.0       1.00      1.00      1.00    120124
        4.0       1.00      1.00      1.00     86565
        5.0       0.99      0.99      0.99     56477
        6.0       0.95      0.95      0.95     35392
        7.0       0.86      0.85      0.86     21734
        8.0       0.66      0.67      0.67     10924
        9.0       0.54      0.55      0.55      8093
       10.0       0.44      0.44      0.44      6280
       11.0       0.36      0.36      0.36      4644
       12.0       0.32      0.31      0.32      3852
       13.0       0.28      0.27      0.28      3024
       14.0       0.24      0.24      0.24      2522
       15.0       0.22      0.22      0.22      2015
       16.0       0.20      0.19      0.19      1767
       17.0       0.17      0.17      0.17      1381
       18.0       0.16      0.15      0.16      1171
avg / total       0.97      0.97      0.97    957887

'''


def sort_file(filename, CORES=4):
    log.info("sort file")
    subprocess.check_output("LC_ALL=C nice sort --parallel=%d --temporary-directory=./tmp/ --output=%s %s" %
        (CORES, filename, filename), shell=True)


def sort_file_random(filename, CORES=4):
    log.info("sort file (random)")
    subprocess.check_output("LC_ALL=C nice sort --random-sort --parallel=%d --temporary-directory=./tmp/ --output=%s %s" %
        (CORES, filename, filename), shell=True)


def keep_lowest_move_count_per_state(filename):
    log.info("keep_lowest_move_count_per_state called")

    filename_tmp = filename + '.tmp'
    with open(filename, 'r') as fh_read:
        with open(filename_tmp, 'w') as fh_tmp:
            prev_state = None
            prev_state_count = None

            for line in fh_read:
                line_list = line.strip().split(',')
                state = ','.join(line_list[0:-1])
                count = line_list[-1]

                count = count.lstrip('0')
                count = int(count)

                if prev_state is None or state != prev_state:
                    fh_tmp.write(line)
                    prev_state_count = count

                elif state == prev_state and count == prev_state_count:
                    fh_tmp.write(line)

                prev_state = state

    os.rename(filename_tmp, filename)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(filename)12s %(levelname)8s: %(message)s')
    log = logging.getLogger(__name__)

    # Color the errors and warnings in red
    logging.addLevelName(logging.ERROR, "\033[91m   %s\033[0m" % logging.getLevelName(logging.ERROR))
    logging.addLevelName(logging.WARNING, "\033[91m %s\033[0m" % logging.getLevelName(logging.WARNING))

    filename = 'centers-444-train.data'
    log.info("create random cubes")
    sort_file(filename)
    keep_lowest_move_count_per_state(filename)
    sort_file_random(filename)
    log.info("finished")

