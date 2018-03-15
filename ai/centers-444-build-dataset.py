#!/usr/bin/env python3

from rubikscubennnsolver import RubiksCube
from rubikscubennnsolver.RubiksCube444 import solved_4x4x4, centers_444, RubiksCube444
from pprint import pformat
import json
import logging
import random
import os
import subprocess
import sys


def randomize(cube, count, fh, threshold):

    if cube.is_even():
        max_rows = int(cube.size/2)
    else:
        max_rows = int((cube.size - 1)/2)

    sides = ['U', 'L', 'F', 'R', 'B', 'D']
    moves = []
    #cube.print_cube()

    for x in range(count):
        cube_state_changed = False
        original_cube_state = cube.state[:]

        while not cube_state_changed:
            rows = random.randint(1, max_rows)
            side_index = random.randint(0, 5)
            side = sides[side_index]
            quarter_turns = random.randint(1, 2)
            clockwise = random.randint(0, 1)

            if rows == 2:
                move = "%sw" % side
            elif rows > 2:
                move = "%d%s" % (rows, side)
            else:
                move = side

            if quarter_turns == 2:
                move += str(quarter_turns)
            elif quarter_turns == 1:
                if not clockwise:
                    move += "'"
            else:
                raise Exception("quarter_turns is %s" % quarter_turns)

            cube.rotate(move)

            if cube.state != original_cube_state:
                cube_state_changed = True
                #log.info("%d: %s did change cube state" % (x, move))
                break
            #else:
            #    log.info("%d: %s did NOT change cube state" % (x, move))

        if x + 1 > threshold:
            UD_cost = cube.lt_UD_centers_solve_unstaged.steps_cost()
            LR_cost = cube.lt_LR_centers_solve_unstaged.steps_cost()
            FB_cost = cube.lt_FB_centers_solve_unstaged.steps_cost()

            UF_cost = cube.lt_UF_centers_solve_unstaged.steps_cost()
            UL_cost = cube.lt_UL_centers_solve_unstaged.steps_cost()
            UR_cost = cube.lt_UR_centers_solve_unstaged.steps_cost()
            UB_cost = cube.lt_UB_centers_solve_unstaged.steps_cost()

            LF_cost = cube.lt_LF_centers_solve_unstaged.steps_cost()
            LB_cost = cube.lt_LB_centers_solve_unstaged.steps_cost()
            LD_cost = cube.lt_LD_centers_solve_unstaged.steps_cost()

            FR_cost = cube.lt_FR_centers_solve_unstaged.steps_cost()
            FD_cost = cube.lt_FD_centers_solve_unstaged.steps_cost()

            RB_cost = cube.lt_RB_centers_solve_unstaged.steps_cost()
            RD_cost = cube.lt_RD_centers_solve_unstaged.steps_cost()

            BD_cost = cube.lt_BD_centers_solve_unstaged.steps_cost()

            out_of_place_count = cube.out_of_place_count()
            out_of_place_cost = out_of_place_count / 8

            center_pairs_count = cube.center_pairs_count()
            center_unpaired_count = 24 - center_pairs_count
            center_unpaired_cost = center_unpaired_count / 8

            ULFRBD_steps = cube.lt_ULFRBD_centers_solve_unstaged.steps()

            if ULFRBD_steps is None:
                cost_to_here = x + 1
                #log.info("ULFRBD_steps None")
            else:
                cost_to_here = len(ULFRBD_steps)

                #if cost_to_here == 0:
                #    cube.print_cube()
                #log.info("ULFRBD_steps %s" % ULFRBD_steps)

            # dwalton

            fh.write("%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%s,%s,%02d\n" %
                (UD_cost, LR_cost, FB_cost,
                 UF_cost, UL_cost, UR_cost, UB_cost,
                 LF_cost,  LB_cost, LD_cost,
                 FR_cost, FD_cost,
                 RB_cost, RD_cost,
                 BD_cost,
                 out_of_place_cost, center_unpaired_cost, cost_to_here))

            '''
            fh.write("%d,%d,%d,%d,%s,%s,%02d\n" %
                (UD_cost, LR_cost, FB_cost,
                 UF_cost,
                 out_of_place_cost, center_unpaired_cost, cost_to_here))
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

    count = int(sys.argv[1])

    filename = 'centers-444.data'
    #threshold = 6
    threshold = 0

    log.info("create random cubes")
    with open(filename, 'w') as fh:
        # 2m 30s for 10k when creating a new cube object each time
        # 2m  4s for 10k when using one cube object
        # 1m 30s for 10k after passing threshold to randomize
        cube = RubiksCube444(solved_4x4x4, 'URFDLB')
        cube.lt_init()
        cube.nuke_corners()
        cube.nuke_edges()
        original_state = cube.state[:]
        original_solution = cube.solution[:]

        for x in range(count):
            randomize(cube, 14, fh, threshold)
            # cube.print_cube()
            cube.state = original_state[:]
            cube.solution = original_solution[:]

            if x % 1000 == 0:
                log.info(x)

    #sort_file(filename)
    #keep_lowest_move_count_per_state(filename)
    sort_file_random(filename)
    log.info("finished")
