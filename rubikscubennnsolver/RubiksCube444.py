#!/usr/bin/env python3

from rubikscubennnsolver import RubiksCube
from rubikscubennnsolver.LookupTable import (
    get_characters_common_count,
    steps_on_same_face_and_layer,
    LookupTable,
    LookupTableCostOnly,
    LookupTableIDA,
)
from pprint import pformat
import logging
import sys

log = logging.getLogger(__name__)


moves_4x4x4 = ("U", "U'", "U2", "Uw", "Uw'", "Uw2",
               "L", "L'", "L2", "Lw", "Lw'", "Lw2",
               "F" , "F'", "F2", "Fw", "Fw'", "Fw2",
               "R" , "R'", "R2", "Rw", "Rw'", "Rw2",
               "B" , "B'", "B2", "Bw", "Bw'", "Bw2",
               "D" , "D'", "D2", "Dw", "Dw'", "Dw2")

solved_4x4x4 = 'UUUUUUUUUUUUUUUURRRRRRRRRRRRRRRRFFFFFFFFFFFFFFFFDDDDDDDDDDDDDDDDLLLLLLLLLLLLLLLLBBBBBBBBBBBBBBBB'

centers_444 = (6, 7, 10, 11, 22, 23, 26, 27, 38, 39, 42, 43, 54, 55, 58, 59, 70, 71, 74, 75, 86, 87, 90, 91)

UD_centers_444 = (6, 7, 10, 11, 86, 87, 90, 91)

LR_centers_444 = (22, 23, 26, 27, 54, 55, 58, 59)

edges_444 = (
    2, 3, 5, 8, 9, 12, 14, 15,      # Upper
    18, 19, 21, 24, 25, 28, 30, 31, # Left
    34, 35, 37, 40, 41, 44, 46, 47, # Front
    50, 51, 53, 56, 57, 60, 62, 63, # Right
    66, 67, 69, 72, 73, 76, 78, 79, # Back
    82, 83, 85, 88, 89, 92, 94, 95) # Down

wings_444 = (
    2, 3,   # Upper
    5, 9,
    8, 12,
    14, 15,
    21, 25, # Left
    24, 28,
    53, 57, # Right
    56, 60,
    82, 83, # Back
    85, 89,
    88, 92,
    94, 95
)

centers_solved_states_444 = set()
centers_solved_states_444.add('UUUULLLLFFFFRRRRBBBBDDDD')
centers_solved_states_444.add('UUUUFFFFRRRRBBBBLLLLDDDD')
centers_solved_states_444.add('UUUURRRRBBBBLLLLFFFFDDDD')
centers_solved_states_444.add('UUUUBBBBLLLLFFFFRRRRDDDD')
centers_solved_states_444.add('DDDDLLLLBBBBRRRRFFFFUUUU')
centers_solved_states_444.add('DDDDBBBBRRRRFFFFLLLLUUUU')
centers_solved_states_444.add('DDDDRRRRFFFFLLLLBBBBUUUU')
centers_solved_states_444.add('DDDDFFFFLLLLBBBBRRRRUUUU')
centers_solved_states_444.add('LLLLUUUUBBBBDDDDFFFFRRRR')
centers_solved_states_444.add('LLLLBBBBDDDDFFFFUUUURRRR')
centers_solved_states_444.add('LLLLDDDDFFFFUUUUBBBBRRRR')
centers_solved_states_444.add('LLLLFFFFUUUUBBBBDDDDRRRR')
centers_solved_states_444.add('FFFFLLLLDDDDRRRRUUUUBBBB')
centers_solved_states_444.add('FFFFDDDDRRRRUUUULLLLBBBB')
centers_solved_states_444.add('FFFFRRRRUUUULLLLDDDDBBBB')
centers_solved_states_444.add('FFFFUUUULLLLDDDDRRRRBBBB')
centers_solved_states_444.add('RRRRDDDDBBBBUUUUFFFFLLLL')
centers_solved_states_444.add('RRRRBBBBUUUUFFFFDDDDLLLL')
centers_solved_states_444.add('RRRRUUUUFFFFDDDDBBBBLLLL')
centers_solved_states_444.add('RRRRFFFFDDDDBBBBUUUULLLL')
centers_solved_states_444.add('BBBBUUUURRRRDDDDLLLLFFFF')
centers_solved_states_444.add('BBBBRRRRDDDDLLLLUUUUFFFF')
centers_solved_states_444.add('BBBBDDDDLLLLUUUURRRRFFFF')
centers_solved_states_444.add('BBBBLLLLUUUURRRRDDDDFFFF')

def centers_solved_444(state):
    if state[0:24] in centers_solved_states_444:
        return True
    return False



def get_best_entry(foo):
    # TODO this can only track wings since it is only used by 4x4x4
    best_entry = None
    best_paired_edges = None
    best_paired_wings = None
    best_steps_len = None

    for (paired_edges, paired_wings, steps_len, state) in foo:
        if (best_entry is None or
            paired_edges > best_paired_edges or
            (paired_edges == best_paired_edges and paired_wings > best_paired_wings) or
            (paired_edges == best_paired_edges and paired_wings == best_paired_wings and steps_len < best_steps_len)):

            best_entry = (paired_edges, paired_wings, steps_len, state)
            best_paired_edges = paired_edges
            best_paired_wings = paired_wings
            best_steps_len = steps_len
    return best_entry


def get_edges_paired_binary_signature(state):
    """
    The facelets are numbered:

                  - 02 03 -
                 05  - -  08
                 09  - -  12
                  - 14 15 -

     - 18 19 -    - 34 35 -    - 50 51 -    - 66 67 -
    21  - -  24  37  - -  40  53  - -  56  69  - -  72
    25  - -  28  41  - -  44  57  - -  60  73  - -  76
     - 30 31 -    - 46 47 -    - 62 63 -    - 78 79 -

                  - 82 83 -
                 85  - -  88
                 89  - -  92
                  - 94 95 -


    The wings are labeled 0123456789abcdefghijklmn

                  -  0 1  -
                  2  - -  3
                  4  - -  5
                  -  6 7 -

     -  2 4  -    -  6 7  -    -  5 3  -    -  1 0  -
     8  - -  9    9  - -  c    c  - -  d    d  - -  8
     a  - -  b    b  - -  e    e  - -  f    f  - -  a
     -  k i  -    -  g h  -    -  j l  -    -  n m  -

                  -  g h  -
                  i  - -  j
                  k  - -  l
                  -  m n  -

    'state' goes wing by # wing and records the location of where the sibling wing is located.

    state: 10425376a8b9ecfdhgkiljnm

    index: 000000000011111111112222
           012345678901234567890123

    get_edges_paired_binary_signature('10425376a8b9ecfdhgkiljnm')
    111111111111

    get_edges_paired_binary_signature('7ad9nlg0j14cbm2i6kfh85e3')
    000000000000
    """
    result = []

    # Upper
    if state[0] == '1':
        result.append('1')
    else:
        result.append('0')

    if state[2] == '4':
        result.append('1')
    else:
        result.append('0')

    if state[4] == '5':
        result.append('1')
    else:
        result.append('0')

    if state[6] == '7':
        result.append('1')
    else:
        result.append('0')

    # Left
    if state[8] == 'a':
        result.append('1')
    else:
        result.append('0')

    if state[10] == 'b':
        result.append('1')
    else:
        result.append('0')

    # Right
    if state[12] == 'e':
        result.append('1')
    else:
        result.append('0')

    if state[14] == 'f':
        result.append('1')
    else:
        result.append('0')

    # Down
    if state[16] == 'h':
        result.append('1')
    else:
        result.append('0')

    if state[18] == 'k':
        result.append('1')
    else:
        result.append('0')

    if state[20] == 'l':
        result.append('1')
    else:
        result.append('0')

    if state[22] == 'n':
        result.append('1')
    else:
        result.append('0')

    return ''.join(result)


'''
lookup-table-4x4x4-step11-UD-centers-stage.txt
lookup-table-4x4x4-step12-LR-centers-stage.txt
lookup-table-4x4x4-step13-FB-centers-stage.txt
==============================================
1 steps has 3 entries (0 percent, 0.00x previous step)
2 steps has 36 entries (0 percent, 12.00x previous step)
3 steps has 484 entries (0 percent, 13.44x previous step)
4 steps has 5,408 entries (0 percent, 11.17x previous step)
5 steps has 48,955 entries (6 percent, 9.05x previous step)
6 steps has 242,011 entries (32 percent, 4.94x previous step)
7 steps has 362,453 entries (49 percent, 1.50x previous step)
8 steps has 75,955 entries (10 percent, 0.21x previous step)
9 steps has 166 entries (0 percent, 0.00x previous step)

Total: 735,471 entries
'''
class LookupTable444UDCentersStageCostOnly(LookupTableCostOnly):

    def __init__(self, parent):

        LookupTableCostOnly.__init__(
            self,
            parent,
            'lookup-table-4x4x4-step11-UD-centers-stage.cost-only.txt',
            'f0000f',
            linecount=735471,
            max_depth=9,
            load_string=False)

    def state(self):
        parent_state = self.parent.state
        result = ''.join(['1' if parent_state[x] in ('U', 'D') else '0' for x in centers_444])
        return int(result, 2)


class LookupTable444LRCentersStageCostOnly(LookupTableCostOnly):

    def __init__(self, parent):
        LookupTableCostOnly.__init__(
            self,
            parent,
            'lookup-table-4x4x4-step12-LR-centers-stage.cost-only.txt',
            '0f0f00',
            linecount=735471,
            max_depth=9,
            load_string=False)

    def state(self):
        parent_state = self.parent.state
        result = ''.join(['1' if parent_state[x] in ('L', 'R') else '0' for x in centers_444])
        return int(result, 2)


class LookupTable444FBCentersStageCostOnly(LookupTableCostOnly):

    def __init__(self, parent):
        LookupTableCostOnly.__init__(
            self,
            parent,
            'lookup-table-4x4x4-step13-FB-centers-stage.cost-only.txt',
            '00f0f0',
            linecount=735471,
            max_depth=9,
            load_string=False)

    def state(self):
        parent_state = self.parent.state
        result = ''.join(['1' if parent_state[x] in ('F', 'B') else '0' for x in centers_444])
        return int(result, 2)



class LookupTableIDA444ULFRBDCentersStage(LookupTableIDA):
    """
    lookup-table-4x4x4-step10-ULFRBD-centers-stage.txt
    ==================================================
    1 steps has 4 entries (0 percent, 0.00x previous step)
    2 steps has 54 entries (0 percent, 13.50x previous step)
    3 steps has 726 entries (0 percent, 13.44x previous step)
    4 steps has 9,300 entries (0 percent, 12.81x previous step)
    5 steps has 121,407 entries (7 percent, 13.05x previous step)
    6 steps has 1,586,554 entries (92 percent, 13.07x previous step)

    Total: 1,718,045 entries
    """

    def __init__(self, parent):
        LookupTableIDA.__init__(
            self,
            parent,
            'lookup-table-4x4x4-step10-ULFRBD-centers-stage.txt',
            'UUUULLLLFFFFLLLLFFFFUUUU',
            moves_4x4x4,

            # illegal_moves...ignoring these increases the average solution
            # by less than 1 move but makes the IDA search about 20x faster
            ("Lw", "Lw'", "Lw2",
             "Bw", "Bw'", "Bw2",
             "Dw", "Dw'", "Dw2"),

            # prune tables
            (parent.lt_UD_centers_stage,
             parent.lt_LR_centers_stage,
             parent.lt_FB_centers_stage),
            linecount=1718045,
            max_depth=6)

    def state(self):
        parent_state = self.parent.state
        result = ''.join(['L' if parent_state[x] in ('L', 'R') else 'F' if parent_state[x] in ('F', 'B') else 'U' for x in centers_444])
        return result


class LookupTable444UDCentersSolveUnstaged(LookupTable):
    """
    lookup-table-4x4x4-step201-UD-centers-solve-unstaged.txt
    ========================================================
    1 steps has 7 entries (0 percent, 0.00x previous step)
    2 steps has 84 entries (0 percent, 12.00x previous step)
    3 steps has 1118 entries (0 percent, 13.31x previous step)
    4 steps has 14208 entries (0 percent, 12.71x previous step)
    5 steps has 163085 entries (0 percent, 11.48x previous step)
    6 steps has 1586257 entries (3 percent, 9.73x previous step)
    7 steps has 10286840 entries (19 percent, 6.48x previous step)
    8 steps has 26985405 entries (52 percent, 2.62x previous step)
    9 steps has 12258437 entries (23 percent, 0.45x previous step)
    10 steps has 187529 entries (0 percent, 0.02x previous step)

    Total: 51482970 entries
    Average: 7.973232 moves
    """
    def __init__(self, parent):

        LookupTable.__init__(
            self,
            parent,
            'lookup-table-4x4x4-step201-UD-centers-solve-unstaged.txt',
            'UUUUxxxxxxxxxxxxxxxxDDDD',
            linecount=51482970,
            max_depth=10)

    def __str__(self):
        return self.__class__.__name__

    def state(self):
        parent_state = self.parent.state
        result = ''.join([parent_state[x] if parent_state[x] in ('U', 'D') else 'x' for x in centers_444])
        return result


class LookupTable444LRCentersSolveUnstaged(LookupTable444UDCentersSolveUnstaged):

    def state(self):
        """
        - rotate cube y'
        - rotate cube x
        - x out everything but L and R
        - change Ls to Us
        - change Rs to Ds
        """
        tmp_state = self.parent.state[:]
        tmp_solution = self.parent.solution[:]

        self.parent.rotate("y'")
        self.parent.rotate("x")
        parent_state = self.parent.state
        result = []

        for square_index in centers_444:
            if parent_state[square_index] == 'L':
                result.append('U')
            elif parent_state[square_index] == 'R':
                result.append('D')
            else:
                result.append('x')

        result = ''.join(result)
        self.parent.state = tmp_state[:]
        self.parent.solution = tmp_solution[:]
        return result


class LookupTable444FBCentersSolveUnstaged(LookupTable444UDCentersSolveUnstaged):

    def state(self):
        """
        - rotate cube x
        - x out everything but F and B
        - change Fs to Us
        - change Bs to Ds
        """
        tmp_state = self.parent.state[:]
        tmp_solution = self.parent.solution[:]

        self.parent.rotate("x")
        parent_state = self.parent.state
        result = []

        for square_index in centers_444:
            if parent_state[square_index] == 'F':
                result.append('U')
            elif parent_state[square_index] == 'B':
                result.append('D')
            else:
                result.append('x')

        result = ''.join(result)
        self.parent.state = tmp_state[:]
        self.parent.solution = tmp_solution[:]
        return result


class LookupTable444UFCentersSolveUnstaged(LookupTable):
    """
    lookup-table-4x4x4-step204-UF-centers-solve-unstaged.txt
    ========================================================
    1 steps has 10 entries (0 percent, 0.00x previous step)
    2 steps has 118 entries (0 percent, 11.80x previous step)
    3 steps has 1,474 entries (0 percent, 12.49x previous step)
    4 steps has 18,198 entries (0 percent, 12.35x previous step)
    5 steps has 209,940 entries (0 percent, 11.54x previous step)
    6 steps has 2,151,856 entries (4 percent, 10.25x previous step)
    7 steps has 14,657,659 entries (28 percent, 6.81x previous step)
    8 steps has 28,677,551 entries (55 percent, 1.96x previous step)
    9 steps has 5,739,465 entries (11 percent, 0.20x previous step)
    10 steps has 26,699 entries (0 percent, 0.00x previous step)

    Total: 51,482,970 entries
    Average: 7.730411 moves
    """

    def __init__(self, parent):
        LookupTable.__init__(
            self,
            parent,
            'lookup-table-4x4x4-step204-UF-centers-solve-unstaged.txt',
            'UUUUxxxxFFFFxxxxxxxxxxxx',
            linecount=51482970,
            max_depth=10)

    def __str__(self):
        return self.__class__.__name__

    def state(self):
        parent_state = self.parent.state
        result = ''.join([parent_state[x] if parent_state[x] in ('U', 'F') else 'x' for x in centers_444])
        return result


class LookupTable444ULCentersSolveUnstaged(LookupTable444UFCentersSolveUnstaged):

    def state(self):
        """
        - rotate cube y'
        - x out everything but U and L
        - change Ls to Fs
        """
        parent_state = self.parent.state
        tmp_state = parent_state[:]
        tmp_solution = self.parent.solution[:]

        self.parent.rotate("y'")
        #for square_index in range(1, self.parent.sideD.max_pos + 1):
        for square_index in centers_444:
            if parent_state[square_index] == 'U':
                pass
            elif parent_state[square_index] == 'L':
                parent_state[square_index] = 'F'
            else:
                parent_state[square_index] = 'x'

        #result = ''.join([parent_state[x] if parent_state[x] in ('U', 'F') else 'x' for x in centers_444])
        result = ''.join([parent_state[x] for x in centers_444])
        self.parent.state = tmp_state[:]
        self.parent.solution = tmp_solution[:]
        #log.info("%s: return %s" % (self, result))
        return result


class LookupTable444URCentersSolveUnstaged(LookupTable444UFCentersSolveUnstaged):

    def state(self):
        """
        - rotate cube y
        - x out everything but U and R
        - change Ls to Fs
        """
        parent_state = self.parent.state
        tmp_state = parent_state[:]
        tmp_solution = self.parent.solution[:]

        self.parent.rotate("y")
        #for square_index in range(1, self.parent.sideD.max_pos + 1):
        for square_index in centers_444:
            if parent_state[square_index] == 'U':
                pass
            elif parent_state[square_index] == 'R':
                parent_state[square_index] = 'F'
            else:
                parent_state[square_index] = 'x'

        #result = ''.join([parent_state[x] if parent_state[x] in ('U', 'F') else 'x' for x in centers_444])
        result = ''.join([parent_state[x] for x in centers_444])
        self.parent.state = tmp_state[:]
        self.parent.solution = tmp_solution[:]
        return result


class LookupTable444UBCentersSolveUnstaged(LookupTable444UFCentersSolveUnstaged):

    def state(self):
        """
        - rotate cube y2
        - x out everything but U and R
        - change Ls to Fs
        """
        parent_state = self.parent.state
        tmp_state = parent_state[:]
        tmp_solution = self.parent.solution[:]

        self.parent.rotate("y")
        self.parent.rotate("y")

        for square_index in centers_444:
            if parent_state[square_index] == 'U':
                pass
            elif parent_state[square_index] == 'B':
                parent_state[square_index] = 'F'
            else:
                parent_state[square_index] = 'x'

        result = ''.join([parent_state[x] for x in centers_444])
        self.parent.state = tmp_state[:]
        self.parent.solution = tmp_solution[:]
        return result


class LookupTable444LFCentersSolveUnstaged(LookupTable444UFCentersSolveUnstaged):

    def state(self):
        parent_state = self.parent.state
        tmp_state = parent_state[:]
        tmp_solution = self.parent.solution[:]

        self.parent.rotate("z")

        for square_index in centers_444:
            if parent_state[square_index] == 'L':
                parent_state[square_index] = 'U'
            elif parent_state[square_index] == 'F':
                pass
            else:
                parent_state[square_index] = 'x'

        result = ''.join([parent_state[x] for x in centers_444])
        self.parent.state = tmp_state[:]
        self.parent.solution = tmp_solution[:]
        return result


class LookupTable444LBCentersSolveUnstaged(LookupTable444UFCentersSolveUnstaged):

    def state(self):
        parent_state = self.parent.state
        tmp_state = parent_state[:]
        tmp_solution = self.parent.solution[:]

        self.parent.rotate("z")
        self.parent.rotate("y")
        self.parent.rotate("y")

        for square_index in centers_444:
            if parent_state[square_index] == 'L':
                parent_state[square_index] = 'U'
            elif parent_state[square_index] == 'B':
                parent_state[square_index] = 'F'
            else:
                parent_state[square_index] = 'x'

        result = ''.join([parent_state[x] for x in centers_444])
        self.parent.state = tmp_state[:]
        self.parent.solution = tmp_solution[:]
        return result


class LookupTable444LDCentersSolveUnstaged(LookupTable444UFCentersSolveUnstaged):

    def state(self):
        parent_state = self.parent.state
        tmp_state = parent_state[:]
        tmp_solution = self.parent.solution[:]

        self.parent.rotate("z")
        self.parent.rotate("y'")

        for square_index in centers_444:
            if parent_state[square_index] == 'L':
                parent_state[square_index] = 'U'
            elif parent_state[square_index] == 'D':
                parent_state[square_index] = 'F'
            else:
                parent_state[square_index] = 'x'

        result = ''.join([parent_state[x] for x in centers_444])
        self.parent.state = tmp_state[:]
        self.parent.solution = tmp_solution[:]
        return result


class LookupTable444FRCentersSolveUnstaged(LookupTable444UFCentersSolveUnstaged):

    def state(self):
        parent_state = self.parent.state
        tmp_state = parent_state[:]
        tmp_solution = self.parent.solution[:]

        self.parent.rotate("z'")

        for square_index in centers_444:
            if parent_state[square_index] == 'R':
                parent_state[square_index] = 'U'
            elif parent_state[square_index] == 'F':
                parent_state[square_index] = 'F'
            else:
                parent_state[square_index] = 'x'

        result = ''.join([parent_state[x] for x in centers_444])
        self.parent.state = tmp_state[:]
        self.parent.solution = tmp_solution[:]
        return result


class LookupTable444FDCentersSolveUnstaged(LookupTable444UFCentersSolveUnstaged):

    def state(self):
        parent_state = self.parent.state
        tmp_state = parent_state[:]
        tmp_solution = self.parent.solution[:]

        self.parent.rotate("z")
        self.parent.rotate("z")

        for square_index in centers_444:
            if parent_state[square_index] == 'D':
                parent_state[square_index] = 'U'
            elif parent_state[square_index] == 'F':
                parent_state[square_index] = 'F'
            else:
                parent_state[square_index] = 'x'

        result = ''.join([parent_state[x] for x in centers_444])
        self.parent.state = tmp_state[:]
        self.parent.solution = tmp_solution[:]
        return result


class LookupTable444RBCentersSolveUnstaged(LookupTable444UFCentersSolveUnstaged):

    def state(self):
        parent_state = self.parent.state
        tmp_state = parent_state[:]
        tmp_solution = self.parent.solution[:]

        self.parent.rotate("z'")
        self.parent.rotate("y")
        self.parent.rotate("y")

        for square_index in centers_444:
            if parent_state[square_index] == 'R':
                parent_state[square_index] = 'U'
            elif parent_state[square_index] == 'B':
                parent_state[square_index] = 'F'
            else:
                parent_state[square_index] = 'x'

        result = ''.join([parent_state[x] for x in centers_444])
        self.parent.state = tmp_state[:]
        self.parent.solution = tmp_solution[:]
        return result


class LookupTable444RDCentersSolveUnstaged(LookupTable444UFCentersSolveUnstaged):

    def state(self):
        parent_state = self.parent.state
        tmp_state = parent_state[:]
        tmp_solution = self.parent.solution[:]

        self.parent.rotate("z'")
        self.parent.rotate("y")

        for square_index in centers_444:
            if parent_state[square_index] == 'R':
                parent_state[square_index] = 'U'
            elif parent_state[square_index] == 'D':
                parent_state[square_index] = 'F'
            else:
                parent_state[square_index] = 'x'

        result = ''.join([parent_state[x] for x in centers_444])
        self.parent.state = tmp_state[:]
        self.parent.solution = tmp_solution[:]
        return result


class LookupTable444BDCentersSolveUnstaged(LookupTable444UFCentersSolveUnstaged):

    def state(self):
        parent_state = self.parent.state
        tmp_state = parent_state[:]
        tmp_solution = self.parent.solution[:]

        self.parent.rotate("z")
        self.parent.rotate("z")
        self.parent.rotate("y")
        self.parent.rotate("y")

        for square_index in centers_444:
            if parent_state[square_index] == 'D':
                parent_state[square_index] = 'U'
            elif parent_state[square_index] == 'B':
                parent_state[square_index] = 'F'
            else:
                parent_state[square_index] = 'x'

        result = ''.join([parent_state[x] for x in centers_444])
        self.parent.state = tmp_state[:]
        self.parent.solution = tmp_solution[:]
        return result


class LookupTableIDA444ULFRBDCentersSolveUnstaged(LookupTableIDA):
    """
    lookup-table-4x4x4-step200-ULFRBD-centers-solve-unstaged.txt
    ============================================================
    1 steps has 10 entries (0 percent, 0.00x previous step)
    2 steps has 162 entries (0 percent, 16.20x previous step)
    3 steps has 2,427 entries (0 percent, 14.98x previous step)
    4 steps has 35,830 entries (0 percent, 14.76x previous step)
    5 steps has 527,561 entries (0 percent, 14.72x previous step)
    6 steps has 7,683,218 entries (6 percent, 14.56x previous step)
    7 steps has 111,158,950 entries (93 percent, 14.47x previous step)

    Total: 119,408,158 entries

    24!/(4!*4!*4!*4!*4!*4!) is 3,246,670,537,000,000
    If the number of entries expands by 14.47 each time (it won't
    but this gives us a rough guess of the distribution) we are
    looking at:

    8 steps 1,608,470,006 (total 1,727,878,164)
    9 steps 23,274,560,986 (total 25,002,439,150)
    10 steps 336,782,897,467 (total 361,785,336,617)
    11 steps 4,873,248,526,347 (total 5,235,033,862,964)
    12 steps 70,515,906,176,241 (total 75,750,940,039,205)
    13 steps 1,020,365,162,370,207 (total 1,096,116,102,409,412)
    14 steps This would put us over 3,246,670,537,000,000

    So an educated guess is that there would be a huge percentage of states
    at 14 steps, I am sure there would be some that were longer than that.
    """
    def __init__(self, parent):

        LookupTableIDA.__init__(
            self,
            parent,
            'lookup-table-4x4x4-step200-ULFRBD-centers-solve-unstaged.txt',
            'UUUULLLLFFFFRRRRBBBBDDDD',
            moves_4x4x4,

            # illegal_moves...ignoring these increases the average solution
            # by less than 1 move but makes the IDA search about 20x faster
            ("Lw", "Lw'", "Lw2",
             "Bw", "Bw'", "Bw2",
             "Dw", "Dw'", "Dw2"),

            # prune tables
            (parent.lt_UD_centers_solve_unstaged,
             parent.lt_LR_centers_solve_unstaged,
             parent.lt_FB_centers_solve_unstaged,

             parent.lt_UF_centers_solve_unstaged,
             parent.lt_UL_centers_solve_unstaged,
             parent.lt_UR_centers_solve_unstaged,
             parent.lt_UB_centers_solve_unstaged,

             parent.lt_LF_centers_solve_unstaged,
             parent.lt_LB_centers_solve_unstaged,
             parent.lt_LD_centers_solve_unstaged,
             parent.lt_FR_centers_solve_unstaged,
             parent.lt_FD_centers_solve_unstaged,

             parent.lt_RB_centers_solve_unstaged,
             parent.lt_RD_centers_solve_unstaged,
             parent.lt_BD_centers_solve_unstaged,
            ),

            linecount=119408158,
            max_depth=7)

    def state(self):
        parent_state = self.parent.state
        result = ''.join([parent_state[x] for x in centers_444])
        return result


class LookupTable444ULFRBDCentersSolve(LookupTable):
    """
    lookup-table-4x4x4-step30-ULFRBD-centers-solve.txt
    ==================================================
    1 steps has 96 entries (0 percent, 0.00x previous step)
    2 steps has 1,008 entries (0 percent, 10.50x previous step)
    3 steps has 8,208 entries (0 percent, 8.14x previous step)
    4 steps has 41,712 entries (2 percent, 5.08x previous step)
    5 steps has 145,560 entries (7 percent, 3.49x previous step)
    6 steps has 321,576 entries (15 percent, 2.21x previous step)
    7 steps has 514,896 entries (25 percent, 1.60x previous step)
    8 steps has 496,560 entries (24 percent, 0.96x previous step)
    9 steps has 324,096 entries (15 percent, 0.65x previous step)
    10 steps has 177,408 entries (8 percent, 0.55x previous step)
    11 steps has 26,880 entries (1 percent, 0.15x previous step)

    Total: 2,058,000 entries
    """

    def __init__(self, parent):
        LookupTable.__init__(
            self,
            parent,
            'lookup-table-4x4x4-step30-ULFRBD-centers-solve.txt',
            'UUUULLLLFFFFRRRRBBBBDDDD',
            linecount=2058000,
            max_depth=11)

    def state(self):
        parent_state = self.parent.state
        result = ''.join([parent_state[x] for x in centers_444])
        return result


class LookupTable444ULFRBDCentersSolvePairTwoEdges(LookupTableIDA):
    """
    IDA search for a centers solution that also happens to pair two or more edges.
    We do this to (drastically) speed up the edges table lookup later. If no
    edges are paired the edges signature is 000000000000 and there are about
    600k of those entries in lookup-table-4x4x4-step110-edges.txt that we will
    have to evaluate.

    If we can pair two though that drops us down to about 40k edge entries to deal with.
    """

    def __init__(self, parent):
        LookupTableIDA.__init__(
            self,
            parent,
            'lookup-table-4x4x4-step60-tsai-phase2-dummy.txt',
            'TBD',
            moves_4x4x4,
            ("Rw", "Rw'", "Lw", "Lw'",
             "Fw", "Fw'", "Bw", "Bw'",
             "Uw", "Uw'", "Dw", "Dw'"),

            # prune tables
            (parent.lt_ULFRBD_centers_solve,),
            linecount=0,
            max_depth=99)

    def state(self):
        state = self.parent.state
        edges = ''.join([state[square_index] for square_index in wings_444])
        centers = ''.join([state[x] for x in centers_444])
        return centers + edges

    def search_complete(self, state, steps_to_here):
        """
        return True if centers are solved and at least 2 edges are paired
        """

        if centers_solved_444(state):
            paired_edges_count = 12 - self.parent.get_non_paired_edges_count()

            if paired_edges_count >= 2:

                if self.avoid_oll and self.parent.center_solution_leads_to_oll_parity():
                    self.parent.state = self.original_state[:]
                    self.parent.solution = self.original_solution[:]
                    log.info("%s: IDA found match but it leads to OLL" % self)
                    return False

                # rotate_xxx() is very fast but it does not append the
                # steps to the solution so put the cube back in original state
                # and execute the steps via a normal rotate() call
                self.parent.state = self.original_state[:]
                self.parent.solution = self.original_solution[:]

                for step in steps_to_here:
                    self.parent.rotate(step)

                return True

        return False


class LookupTable444ULFRBDCentersSolveEdgesStage(LookupTableIDA):
    """
    Experiment to IDA search until we find a solution that happens to put
    the edges in a state that are in our edge table

    This is sloooow
    """

    def __init__(self, parent):
        LookupTableIDA.__init__(
            self,
            parent,
            'lookup-table-4x4x4-step60-tsai-phase2-dummy.txt',
            'TBD',
            moves_4x4x4,
            ("Rw", "Rw'", "Lw", "Lw'",
             "Fw", "Fw'", "Bw", "Bw'",
             "Uw", "Uw'", "Dw", "Dw'"),

            # prune tables
            (parent.lt_ULFRBD_centers_solve,),
            linecount=0,
            max_depth=99)

    def state(self):
        state = edges_recolor_pattern_444(self.parent.state[:])

        edges = ''.join([state[square_index] for square_index in wings_444])
        centers = ''.join([state[x] for x in centers_444])

        return centers + edges

    def search_complete(self, state, steps_to_here):

        if centers_solved_444(state) and self.parent.solve_all_edges_444(use_bfs=False, apply_steps_if_found=False):

            if self.parent.center_solution_leads_to_oll_parity():
                self.parent.state = self.original_state[:]
                self.parent.solution = self.original_solution[:]
                log.info("%s: IDA found match but it leads to OLL" % self)
                return False

            tmp_state = self.parent.state[:]
            tmp_solution = self.parent.solution[:]
            self.parent.solve_all_edges_444(use_bfs=False, apply_steps_if_found=True)

            if self.parent.edge_solution_leads_to_pll_parity():
                self.parent.state = self.original_state[:]
                self.parent.solution = self.original_solution[:]
                log.info("%s: IDA found match but it leads to PLL" % self)
                return False

            self.parent.state = tmp_state
            self.parent.solution = tmp_solution

            # rotate_xxx() is very fast but it does not append the
            # steps to the solution so put the cube back in original state
            # and execute the steps via a normal rotate() call
            self.parent.state = self.original_state[:]
            self.parent.solution = self.original_solution[:]

            for step in steps_to_here:
                self.parent.rotate(step)

            return True

        return False


wings_for_edges_recolor_pattern_444 = (
    ('0', 2, 67),  # upper
    ('1', 3, 66),
    ('2', 5, 18),
    ('3', 8, 51),
    ('4', 9, 19),
    ('5', 12, 50),
    ('6', 14, 34),
    ('7', 15, 35),

    ('8', 21, 72), # left
    ('9', 24, 37),
    ('a', 25, 76),
    ('b', 28, 41),

    ('c', 53, 40), # right
    ('d', 56, 69),
    ('e', 57, 44),
    ('f', 60, 73),

    ('g', 82, 46), # down
    ('h', 83, 47),
    ('i', 85, 31),
    ('j', 88, 62),
    ('k', 89, 30),
    ('l', 92, 63),
    ('m', 94, 79),
    ('n', 95, 78))


def edges_recolor_pattern_444(state):
    edge_map = {
        'BD': [],
        'BL': [],
        'BR': [],
        'BU': [],
        'DF': [],
        'DL': [],
        'DR': [],
        'FL': [],
        'FR': [],
        'FU': [],
        'LU': [],
        'RU': []
    }

    # Record the two edge_indexes for each of the 12 edges
    for (edge_index, square_index, partner_index) in wings_for_edges_recolor_pattern_444:
        square_value = state[square_index]
        partner_value = state[partner_index]
        wing_str = ''.join(sorted([square_value, partner_value]))
        edge_map[wing_str].append(edge_index)

    # Where is the other wing_str like us?
    for (edge_index, square_index, partner_index) in wings_for_edges_recolor_pattern_444:
        square_value = state[square_index]
        partner_value = state[partner_index]
        wing_str = ''.join(sorted([square_value, partner_value]))

        for tmp_index in edge_map[wing_str]:
            if tmp_index != edge_index:
                state[square_index] = tmp_index
                state[partner_index] = tmp_index
                break
        else:
            raise Exception("could not find tmp_index")

    return ''.join(state)


class LookupTable444Edges(LookupTable):
    """
    lookup-table-4x4x4-step110-edges.txt (11-deep)
    ==============================================
    2 steps has 1 entries (0 percent, 0.00x previous step)
    5 steps has 432 entries (0 percent, 432.00x previous step)
    6 steps has 2,053 entries (0 percent, 4.75x previous step)
    7 steps has 15,475 entries (0 percent, 7.54x previous step)
    8 steps has 151,530 entries (0 percent, 9.79x previous step)
    9 steps has 991,027 entries (1 percent, 6.54x previous step)
    10 steps has 6,203,073 entries (9 percent, 6.26x previous step)
    11 steps has 56,560,361 entries (88 percent, 9.12x previous step)

    Total: 63,923,952 entries
    Average: 10.863674 moves
    """

    def __init__(self, parent):
        LookupTable.__init__(
            self,
            parent,
            'lookup-table-4x4x4-step110-edges.txt',
            '111111111111_10425376a8b9ecfdhgkiljnm',
            linecount=7363591) # 10-deep
            #linecount=63923952) # 11-deep


class RubiksCube444(RubiksCube):

    def __init__(self, state, order, colormap=None, avoid_pll=True, debug=False):
        RubiksCube.__init__(self, state, order, colormap, debug)
        self.avoid_pll = avoid_pll

        if debug:
            log.setLevel(logging.DEBUG)

    def phase(self):
        if self._phase is None:
            self._phase = 'Stage UD centers'
            return self._phase

        if self._phase == 'Stage UD centers':
            if self.UD_centers_staged():
                self._phase = 'Stage LR centers'
            return self._phase

        if self._phase == 'Stage LR centers':
            if self.LR_centers_staged():
                self._phase = 'Solve Centers'

        if self._phase == 'Solve Centers':
            if self.centers_solved():
                self._phase = 'Pair Edges'

        if self._phase == 'Pair Edges':
            if not self.get_non_paired_edges():
                self._phase = 'Solve 3x3x3'

        return self._phase

    def sanity_check(self):
        corners = (1, 4, 13, 16,
                   17, 20, 29, 32,
                   33, 36, 45, 48,
                   49, 52, 61, 64,
                   65, 68, 77, 80,
                   81, 84, 93, 96)

        centers = (6, 7, 10, 11,
                   22, 23, 26, 27,
                   38, 39, 42, 43,
                   54, 55, 58, 59,
                   70, 71, 74, 75,
                   86, 87, 90, 91)

        edge_orbit_0 = (2, 3, 8, 12, 15, 14, 9, 5,
                        18, 19, 24, 28, 31, 30, 25, 21,
                        34, 35, 40, 44, 47, 46, 41, 37,
                        50, 51, 56, 60, 62, 63, 57, 53,
                        66, 67, 72, 76, 79, 78, 73, 69,
                        82, 83, 88, 92, 95, 94, 89, 85)

        self._sanity_check('corners', corners, 4)
        self._sanity_check('centers', centers, 4)
        self._sanity_check('edge-orbit-0', edge_orbit_0, 8)

    def lt_init(self):
        if self.lt_init_called:
            return
        self.lt_init_called = True

        # experiment
        self.lt_UD_centers_solve_unstaged = LookupTable444UDCentersSolveUnstaged(self)
        self.lt_LR_centers_solve_unstaged = LookupTable444LRCentersSolveUnstaged(self)
        self.lt_FB_centers_solve_unstaged = LookupTable444FBCentersSolveUnstaged(self)

        # build these prune tables via the UF table
        # - UL, UF, UR, UB
        # - LF, LB, LD
        # - FR, FD
        # - RB, RD
        # - BD
        self.lt_UF_centers_solve_unstaged = LookupTable444UFCentersSolveUnstaged(self)
        self.lt_UL_centers_solve_unstaged = LookupTable444ULCentersSolveUnstaged(self)
        self.lt_UR_centers_solve_unstaged = LookupTable444URCentersSolveUnstaged(self)
        self.lt_UB_centers_solve_unstaged = LookupTable444UBCentersSolveUnstaged(self)

        self.lt_LF_centers_solve_unstaged = LookupTable444LFCentersSolveUnstaged(self)
        self.lt_LB_centers_solve_unstaged = LookupTable444LBCentersSolveUnstaged(self)
        self.lt_LD_centers_solve_unstaged = LookupTable444LDCentersSolveUnstaged(self)

        self.lt_FR_centers_solve_unstaged = LookupTable444FRCentersSolveUnstaged(self)
        self.lt_FD_centers_solve_unstaged = LookupTable444FDCentersSolveUnstaged(self)

        self.lt_RB_centers_solve_unstaged = LookupTable444RBCentersSolveUnstaged(self)
        self.lt_RD_centers_solve_unstaged = LookupTable444RDCentersSolveUnstaged(self)

        self.lt_BD_centers_solve_unstaged = LookupTable444BDCentersSolveUnstaged(self)

        '''
2018-06-02 22:25:05,277 RubiksCube444.py     INFO: 4x4x4: Start of Phase1
2018-06-02 22:25:05,467   LookupTable.py     INFO: 4x4x4-step200-ULFRBD-centers-solve-unstaged: IDA threshold range 9->99
2018-06-02 22:25:05,469   LookupTable.py     INFO: 4x4x4-step200-ULFRBD-centers-solve-unstaged: IDA threshold 9, explored 1 nodes, took 1ms
2018-06-02 22:25:08,179   LookupTable.py     INFO: 4x4x4-step200-ULFRBD-centers-solve-unstaged: IDA threshold 10, explored 28 nodes, took 0:00:02.709954
2018-06-02 22:26:20,372   LookupTable.py     INFO: 4x4x4-step200-ULFRBD-centers-solve-unstaged: IDA threshold 11, explored 930 nodes, took 0:01:12.193152
        '''
        self.lt_ULFRBD_centers_solve_unstaged = LookupTableIDA444ULFRBDCentersSolveUnstaged(self)
        #self.lt_ULFRBD_centers_solve_unstaged.avoid_oll = True

        # ==============
        # Phase 1 tables
        # ==============
        # prune tables

        # Solving 50 cubes where you binary search through the prune table files takes 57s
        # Solving 50 cubes using the cost-only tables takes 30s!!
        self.lt_UD_centers_stage = LookupTable444UDCentersStageCostOnly(self)
        self.lt_LR_centers_stage = LookupTable444LRCentersStageCostOnly(self)
        self.lt_FB_centers_stage = LookupTable444FBCentersStageCostOnly(self)

        # Stage all centers via IDA
        self.lt_ULFRBD_centers_stage = LookupTableIDA444ULFRBDCentersStage(self)
        self.lt_ULFRBD_centers_stage.avoid_oll = True

        # =============
        # Phase2 tables
        # =============
        self.lt_ULFRBD_centers_solve = LookupTable444ULFRBDCentersSolve(self)
        self.lt_ULFRBD_centers_solve_pair_two_edges = LookupTable444ULFRBDCentersSolvePairTwoEdges(self)
        #self.lt_ULFRBD_centers_solve_edges_stage = LookupTable444ULFRBDCentersSolveEdgesStage(self)

        # Edges table
        self.lt_edges = LookupTable444Edges(self)

    def group_centers_guts(self):
        self.lt_init()

        # If the centers are already solved then return and let group_edges() pair the edges
        if self.centers_solved():
            return

        log.info("%s: Start of Phase1" % self)
        #self.lt_ULFRBD_centers_solve_unstaged.dwalton_solve()
        #self.rotate_for_best_centers_solving()
        #self.print_cube()
        #log.info("%s: middle of Phase1, %d steps in" % (self, self.get_solution_len_minus_rotates(self.solution)))

        self.lt_ULFRBD_centers_solve_unstaged.solve()
        self.print_cube()
        log.info("%s: End of Phase1, %d steps in" % (self, self.get_solution_len_minus_rotates(self.solution)))

        '''
        # Stage all centers then solve all centers...averages 18.12 moves
        log.info("%s: Start of Phase1" % self)
        #self.lt_ULFRBD_centers_stage.ida_all_the_way = True
        #self.lt_ULFRBD_centers_stage.solve()
        self.lt_ULFRBD_centers_stage.dwalton_solve()
        self.rotate_for_best_centers_solving()
        self.print_cube()
        #self.print_solution()
        log.info("%s: End of Phase1, %d steps in" % (self, self.get_solution_len_minus_rotates(self.solution)))
        log.info("")

        # If the centers were already staged we may not be able to avoid OLL when solving the centers
        if self.get_solution_len_minus_rotates(self.solution) == 0:
            self.lt_ULFRBD_centers_solve_pair_two_edges.avoid_oll = False
        else:
            self.lt_ULFRBD_centers_solve_pair_two_edges.avoid_oll = True

        log.info("%s: Start of Phase2, %d steps in" % (self, self.get_solution_len_minus_rotates(self.solution)))
        #self.lt_ULFRBD_centers_solve.solve()
        self.lt_ULFRBD_centers_solve_pair_two_edges.solve()

        # This will IDA search for a centers solution that happens to put the
        # edges in a state that are in our table.  It works and produces
        # solutions in the 50-53 range but can take a few minutes.
        #self.lt_ULFRBD_centers_solve_edges_stage.solve()
        self.rotate_U_to_U()
        self.rotate_F_to_F()
        self.print_cube()
        log.info("%s: End of Phase2, %d steps in" % (self, self.get_solution_len_minus_rotates(self.solution)))
        log.info("")
        '''

    def solve_all_edges_444(self, use_bfs, apply_steps_if_found):

        # Remember what things looked like
        original_state = self.state[:]
        original_solution = self.solution[:]

        outer_layer_moves = (
            "U", "U'", "U2",
            "L", "L'", "L2",
            "F", "F'", "F2",
            "R", "R'", "R2",
            "B", "B'", "B2",
            "D", "D'", "D2",
        )
        pre_steps_to_try = []
        pre_steps_to_try.append([])

        if use_bfs:
            for step in outer_layer_moves:
                pre_steps_to_try.append([step,])

            for step1 in outer_layer_moves:
                for step2 in outer_layer_moves:
                    if not steps_on_same_face_and_layer(step1, step2):
                        pre_steps_to_try.append([step1, step2])

            for step1 in outer_layer_moves:
                for step2 in outer_layer_moves:
                    if not steps_on_same_face_and_layer(step1, step2):

                        for step3 in outer_layer_moves:
                            if not steps_on_same_face_and_layer(step2, step3):
                                pre_steps_to_try.append([step1, step2, step3])

            '''
            for step1 in outer_layer_moves:
                for step2 in outer_layer_moves:
                    if not steps_on_same_face_and_layer(step1, step2):
                        for step3 in outer_layer_moves:
                            if not steps_on_same_face_and_layer(step2, step3):
                                for step4 in outer_layer_moves:
                                    if not steps_on_same_face_and_layer(step3, step4):
                                        pre_steps_to_try.append([step1, step2, step3, step4])

            '''
            log.warning("%d pre_steps_to_try" % len(pre_steps_to_try))

        for pre_steps in pre_steps_to_try:
            #log.info("solve_all_edges_444 trying pre_steps %s" % ' '.join(pre_steps))

            self.state = original_state[:]
            self.solution = original_solution[:]

            for step in pre_steps:
                self.rotate(step)

            state = edges_recolor_pattern_444(self.state[:])

            edges_state = ''.join([state[square_index] for square_index in wings_444])
            signature = get_edges_paired_binary_signature(edges_state)
            signature_width = len(signature) + 1
            edges_state = signature + '_' + edges_state


            # If our state is in lookup-table-4x4x4-step100-edges.txt then execute
            # those steps and we are done
            steps = self.lt_edges.steps(edges_state)

            if steps is not None:

                if apply_steps_if_found:
                    for step in steps:
                        self.rotate(step)
                else:
                    self.state = original_state[:]
                    self.solution = original_solution[:]

                return True

        self.state = original_state[:]
        self.solution = original_solution[:]

        return False

    def solve_edges_six_then_six(self):

        if self.edges_paired():
            return True

        state = edges_recolor_pattern_444(self.state[:])

        edges_state = ''.join([state[square_index] for square_index in wings_444])
        signature = get_edges_paired_binary_signature(edges_state)
        signature_width = len(signature) + 1
        edges_state = signature + '_' + edges_state

        # If our state is in lookup-table-4x4x4-step100-edges.txt then execute
        # those steps and we are done
        steps = self.lt_edges.steps(edges_state)

        if steps is not None:
            for step in steps:
                self.rotate(step)
                return True

        # If we are here then we need to look through lookup-table-4x4x4-step100-edges.txt
        # to find the line whose state is the closest match to our own. This allows us to
        # pair some of our unpaired edges and make some progress even though our current
        # state isn't in the lookup table.
        MAX_WING_PAIRS = 12
        MAX_EDGES = 12

        # It takes 12 steps to solve PLL
        PLL_PENALTY = 12

        STATE_TARGET = '111111111111_10425376a8b9ecfdhgkiljnm'

        original_state = self.state[:]
        original_solution = self.solution[:]
        loop_count = 0

        while not self.edges_paired():

            # How many edges are paired?
            pre_non_paired_edges_count = self.get_non_paired_edges_count()
            pre_paired_edges_count = MAX_WING_PAIRS - pre_non_paired_edges_count

            state = edges_recolor_pattern_444(self.state[:])

            edges_state = ''.join([state[square_index] for square_index in wings_444])
            signature = get_edges_paired_binary_signature(edges_state)
            signature_width = len(signature) + 1
            edges_state = signature + '_' + edges_state

            log.info("%s: solve_edges_six_then_six loop %d: signature %s, edges_paired %d" % (self, loop_count, signature, pre_paired_edges_count))

            # Find all of the 'loose' matching entries in our lookup table. 'loose' means the
            # entry will not unpair any of our already paired wings.
            loose_matching_entry = []
            max_wing_pair_count = None

            # This runs much faster (than find_edge_entries_with_loose_signature) because
            # it is only looking over the signatures that are an exact match instead of a
            # loose match. It produces slightly longer solutions but in about 1/6 the time.
            log.info("%s: find_edge_entries_with_signature start" % self)
            lines_to_examine = self.lt_edges.find_edge_entries_with_signature(signature)
            log.info("%s: find_edge_entries_with_signature end (found %d)" % (self, len(lines_to_examine)))

            for line in lines_to_examine:
                (phase1_state, phase1_steps) = line.split(':')

                common_count = get_characters_common_count(edges_state,
                                                           phase1_state,
                                                           signature_width)
                wing_pair_count = int(common_count/2)

                # Only bother with this entry if it will pair more wings than are currently paired
                if wing_pair_count > pre_paired_edges_count:

                    if max_wing_pair_count is None:
                        loose_matching_entry.append((wing_pair_count, line))
                        max_wing_pair_count = wing_pair_count

                    elif wing_pair_count > max_wing_pair_count:
                        #loose_matching_entry = []
                        loose_matching_entry.append((wing_pair_count, line))
                        max_wing_pair_count = wing_pair_count

                    elif wing_pair_count == max_wing_pair_count:
                        loose_matching_entry.append((wing_pair_count, line))

            log.info("%s: loose_matching_entry %d" % (self, len(loose_matching_entry)))
            #log.warning("loose_matching_entry(%d):\n%s\n" %
            #    (len(loose_matching_entry), pformat(loose_matching_entry)))
            best_score_states = []

            # Now run through each state:steps in loose_matching_entry
            for (wing_pair_count, line) in loose_matching_entry:
                self.state = original_state[:]
                self.solution = original_solution[:]

                (phase1_edges_state_fake, phase1_steps) = line.split(':')
                phase1_steps = phase1_steps.split()

                # Apply the phase1 steps
                for step in phase1_steps:
                    self.rotate(step)

                phase1_state = edges_recolor_pattern_444(self.state[:])
                phase1_edges_state = ''.join([phase1_state[square_index] for square_index in wings_444])
                phase1_signature = get_edges_paired_binary_signature(phase1_edges_state)
                phase1_edges_state = phase1_signature + '_' + phase1_edges_state

                # If that got us to our state_target then phase1 alone paired all
                # of the edges...this is unlikely
                if phase1_edges_state == STATE_TARGET:
                    if self.edge_solution_leads_to_pll_parity():
                        #best_score_states.append((MAX_EDGES, MAX_WING_PAIRS, len(phase1_steps) + PLL_PENALTY, phase1_steps[:]))
                        pass
                    else:
                        best_score_states.append((MAX_EDGES, MAX_WING_PAIRS, len(phase1_steps), phase1_steps[:]))

                else:
                    # phase1_steps did not pair all edges so do another lookup and execute those steps
                    phase2_steps = self.lt_edges.steps(phase1_edges_state)

                    if phase2_steps is not None:
                        for step in phase2_steps:
                            self.rotate(step)

                        phase2_state = edges_recolor_pattern_444(self.state[:])
                        phase2_edges_state = ''.join([phase2_state[square_index] for square_index in wings_444])
                        phase2_signature = get_edges_paired_binary_signature(phase2_edges_state)
                        phase2_edges_state = phase2_signature + '_' + phase2_edges_state
                        phase12_steps = phase1_steps + phase2_steps

                        if phase2_edges_state == STATE_TARGET:

                            if self.edge_solution_leads_to_pll_parity():
                                #best_score_states.append((MAX_EDGES, MAX_WING_PAIRS, len(phase12_steps) + PLL_PENALTY, phase12_steps[:]))
                                pass
                            else:
                                best_score_states.append((MAX_EDGES, MAX_WING_PAIRS, len(phase12_steps), phase12_steps[:]))
                        else:
                            post_non_paired_edges_count = self.get_non_paired_edges_count()
                            paired_edges_count = MAX_WING_PAIRS - post_non_paired_edges_count

                            best_score_states.append((paired_edges_count, paired_edges_count, len(phase12_steps), phase12_steps[:]))
                    else:
                        post_non_paired_edges_count = self.get_non_paired_edges_count()
                        paired_edges_count = MAX_WING_PAIRS - post_non_paired_edges_count

                        best_score_states.append((paired_edges_count, paired_edges_count, len(phase1_steps), phase1_steps[:]))

                #log.info("HERE 10 %s: %s, %s, phase1_edges_state %s, phase2 steps %s" %
                #    (self, wing_pair_count, line, phase1_edges_state, pformat(phase2_steps)))

            #log.info("best_score_states:\n%s" % pformat(best_score_states))
            best_entry = get_best_entry(best_score_states)
            #log.info("best_entry: %s" % pformat(best_entry))

            self.state = original_state[:]
            self.solution = original_solution[:]

            for step in best_entry[3]:
                self.rotate(step)

            original_state = self.state[:]
            original_solution = self.solution[:]

            log.info("%s: solve_edges_six_then_six loop %d: went from %d edges to %d edges in %d moves" %
                (self, loop_count, pre_paired_edges_count, best_entry[0], len(best_entry[3])))
            loop_count += 1

    def group_edges(self):

        if self.edges_paired():
            self.solution.append('EDGES_GROUPED')
            return

        self.lt_init()

        # use_bfs needs more testing...I'm not sure it buys us much
        if not self.solve_all_edges_444(use_bfs=False, apply_steps_if_found=True):
            self.solve_edges_six_then_six()

        log.info("%s: edges paired, %d steps in" % (self, self.get_solution_len_minus_rotates(self.solution)))
        self.solution.append('EDGES_GROUPED')

    def center_pairs_count(self):
        result = 0

        for (a, b, c, d) in (
            (6, 7, 10, 11),
            (22, 23, 26, 27),
            (38, 39, 42, 43),
            (54, 55, 58, 59),
            (70, 71, 74, 75),
            (86, 87, 90, 91)):

            # 2 rows
            if self.state[a] == self.state[b] and self.state[c] == self.state[d]:
                result += 2

            # 2 cols
            elif self.state[a] == self.state[c] and self.state[b] == self.state[d]:
                result += 2

            # 1 row
            elif self.state[a] == self.state[b] or self.state[c] == self.state[d]:
                result += 1

            # 1 col
            elif self.state[a] == self.state[c] or self.state[b] == self.state[d]:
                result += 1

        return result


def rotate_444_U(cube):
    return [cube[0],cube[13],cube[9],cube[5],cube[1],cube[14],cube[10],cube[6],cube[2],cube[15],cube[11],cube[7],cube[3],cube[16],cube[12],cube[8],cube[4]] + cube[33:37] + cube[21:33] + cube[49:53] + cube[37:49] + cube[65:69] + cube[53:65] + cube[17:21] + cube[69:97]

def rotate_444_U_prime(cube):
    return [cube[0],cube[4],cube[8],cube[12],cube[16],cube[3],cube[7],cube[11],cube[15],cube[2],cube[6],cube[10],cube[14],cube[1],cube[5],cube[9],cube[13]] + cube[65:69] + cube[21:33] + cube[17:21] + cube[37:49] + cube[33:37] + cube[53:65] + cube[49:53] + cube[69:97]

def rotate_444_U2(cube):
    return [cube[0],cube[16],cube[15],cube[14],cube[13],cube[12],cube[11],cube[10],cube[9],cube[8],cube[7],cube[6],cube[5],cube[4],cube[3],cube[2],cube[1]] + cube[49:53] + cube[21:33] + cube[65:69] + cube[37:49] + cube[17:21] + cube[53:65] + cube[33:37] + cube[69:97]

def rotate_444_Uw(cube):
    return [cube[0],cube[13],cube[9],cube[5],cube[1],cube[14],cube[10],cube[6],cube[2],cube[15],cube[11],cube[7],cube[3],cube[16],cube[12],cube[8],cube[4]] + cube[33:41] + cube[25:33] + cube[49:57] + cube[41:49] + cube[65:73] + cube[57:65] + cube[17:25] + cube[73:97]

def rotate_444_Uw_prime(cube):
    return [cube[0],cube[4],cube[8],cube[12],cube[16],cube[3],cube[7],cube[11],cube[15],cube[2],cube[6],cube[10],cube[14],cube[1],cube[5],cube[9],cube[13]] + cube[65:73] + cube[25:33] + cube[17:25] + cube[41:49] + cube[33:41] + cube[57:65] + cube[49:57] + cube[73:97]

def rotate_444_Uw2(cube):
    return [cube[0],cube[16],cube[15],cube[14],cube[13],cube[12],cube[11],cube[10],cube[9],cube[8],cube[7],cube[6],cube[5],cube[4],cube[3],cube[2],cube[1]] + cube[49:57] + cube[25:33] + cube[65:73] + cube[41:49] + cube[17:25] + cube[57:65] + cube[33:41] + cube[73:97]

def rotate_444_L(cube):
    return [cube[0],cube[80]] + cube[2:5] + [cube[76]] + cube[6:9] + [cube[72]] + cube[10:13] + [cube[68]] + cube[14:17] + [cube[29],cube[25],cube[21],cube[17],cube[30],cube[26],cube[22],cube[18],cube[31],cube[27],cube[23],cube[19],cube[32],cube[28],cube[24],cube[20],cube[1]] + cube[34:37] + [cube[5]] + cube[38:41] + [cube[9]] + cube[42:45] + [cube[13]] + cube[46:68] + [cube[93]] + cube[69:72] + [cube[89]] + cube[73:76] + [cube[85]] + cube[77:80] + [cube[81],cube[33]] + cube[82:85] + [cube[37]] + cube[86:89] + [cube[41]] + cube[90:93] + [cube[45]] + cube[94:97]

def rotate_444_L_prime(cube):
    return [cube[0],cube[33]] + cube[2:5] + [cube[37]] + cube[6:9] + [cube[41]] + cube[10:13] + [cube[45]] + cube[14:17] + [cube[20],cube[24],cube[28],cube[32],cube[19],cube[23],cube[27],cube[31],cube[18],cube[22],cube[26],cube[30],cube[17],cube[21],cube[25],cube[29],cube[81]] + cube[34:37] + [cube[85]] + cube[38:41] + [cube[89]] + cube[42:45] + [cube[93]] + cube[46:68] + [cube[13]] + cube[69:72] + [cube[9]] + cube[73:76] + [cube[5]] + cube[77:80] + [cube[1],cube[80]] + cube[82:85] + [cube[76]] + cube[86:89] + [cube[72]] + cube[90:93] + [cube[68]] + cube[94:97]

def rotate_444_L2(cube):
    return [cube[0],cube[81]] + cube[2:5] + [cube[85]] + cube[6:9] + [cube[89]] + cube[10:13] + [cube[93]] + cube[14:17] + [cube[32],cube[31],cube[30],cube[29],cube[28],cube[27],cube[26],cube[25],cube[24],cube[23],cube[22],cube[21],cube[20],cube[19],cube[18],cube[17],cube[80]] + cube[34:37] + [cube[76]] + cube[38:41] + [cube[72]] + cube[42:45] + [cube[68]] + cube[46:68] + [cube[45]] + cube[69:72] + [cube[41]] + cube[73:76] + [cube[37]] + cube[77:80] + [cube[33],cube[1]] + cube[82:85] + [cube[5]] + cube[86:89] + [cube[9]] + cube[90:93] + [cube[13]] + cube[94:97]

def rotate_444_Lw(cube):
    return [cube[0],cube[80],cube[79]] + cube[3:5] + [cube[76],cube[75]] + cube[7:9] + [cube[72],cube[71]] + cube[11:13] + [cube[68],cube[67]] + cube[15:17] + [cube[29],cube[25],cube[21],cube[17],cube[30],cube[26],cube[22],cube[18],cube[31],cube[27],cube[23],cube[19],cube[32],cube[28],cube[24],cube[20]] + cube[1:3] + cube[35:37] + cube[5:7] + cube[39:41] + cube[9:11] + cube[43:45] + cube[13:15] + cube[47:67] + [cube[94],cube[93]] + cube[69:71] + [cube[90],cube[89]] + cube[73:75] + [cube[86],cube[85]] + cube[77:79] + [cube[82],cube[81]] + cube[33:35] + cube[83:85] + cube[37:39] + cube[87:89] + cube[41:43] + cube[91:93] + cube[45:47] + cube[95:97]

def rotate_444_Lw_prime(cube):
    return [cube[0]] + cube[33:35] + cube[3:5] + cube[37:39] + cube[7:9] + cube[41:43] + cube[11:13] + cube[45:47] + cube[15:17] + [cube[20],cube[24],cube[28],cube[32],cube[19],cube[23],cube[27],cube[31],cube[18],cube[22],cube[26],cube[30],cube[17],cube[21],cube[25],cube[29]] + cube[81:83] + cube[35:37] + cube[85:87] + cube[39:41] + cube[89:91] + cube[43:45] + cube[93:95] + cube[47:67] + [cube[14],cube[13]] + cube[69:71] + [cube[10],cube[9]] + cube[73:75] + [cube[6],cube[5]] + cube[77:79] + [cube[2],cube[1],cube[80],cube[79]] + cube[83:85] + [cube[76],cube[75]] + cube[87:89] + [cube[72],cube[71]] + cube[91:93] + [cube[68],cube[67]] + cube[95:97]

def rotate_444_Lw2(cube):
    return [cube[0]] + cube[81:83] + cube[3:5] + cube[85:87] + cube[7:9] + cube[89:91] + cube[11:13] + cube[93:95] + cube[15:17] + [cube[32],cube[31],cube[30],cube[29],cube[28],cube[27],cube[26],cube[25],cube[24],cube[23],cube[22],cube[21],cube[20],cube[19],cube[18],cube[17],cube[80],cube[79]] + cube[35:37] + [cube[76],cube[75]] + cube[39:41] + [cube[72],cube[71]] + cube[43:45] + [cube[68],cube[67]] + cube[47:67] + [cube[46],cube[45]] + cube[69:71] + [cube[42],cube[41]] + cube[73:75] + [cube[38],cube[37]] + cube[77:79] + [cube[34],cube[33]] + cube[1:3] + cube[83:85] + cube[5:7] + cube[87:89] + cube[9:11] + cube[91:93] + cube[13:15] + cube[95:97]

def rotate_444_F(cube):
    return cube[0:13] + [cube[32],cube[28],cube[24],cube[20]] + cube[17:20] + [cube[81]] + cube[21:24] + [cube[82]] + cube[25:28] + [cube[83]] + cube[29:32] + [cube[84],cube[45],cube[41],cube[37],cube[33],cube[46],cube[42],cube[38],cube[34],cube[47],cube[43],cube[39],cube[35],cube[48],cube[44],cube[40],cube[36],cube[13]] + cube[50:53] + [cube[14]] + cube[54:57] + [cube[15]] + cube[58:61] + [cube[16]] + cube[62:81] + [cube[61],cube[57],cube[53],cube[49]] + cube[85:97]

def rotate_444_F_prime(cube):
    return cube[0:13] + [cube[49],cube[53],cube[57],cube[61]] + cube[17:20] + [cube[16]] + cube[21:24] + [cube[15]] + cube[25:28] + [cube[14]] + cube[29:32] + [cube[13],cube[36],cube[40],cube[44],cube[48],cube[35],cube[39],cube[43],cube[47],cube[34],cube[38],cube[42],cube[46],cube[33],cube[37],cube[41],cube[45],cube[84]] + cube[50:53] + [cube[83]] + cube[54:57] + [cube[82]] + cube[58:61] + [cube[81]] + cube[62:81] + [cube[20],cube[24],cube[28],cube[32]] + cube[85:97]

def rotate_444_F2(cube):
    return cube[0:13] + [cube[84],cube[83],cube[82],cube[81]] + cube[17:20] + [cube[61]] + cube[21:24] + [cube[57]] + cube[25:28] + [cube[53]] + cube[29:32] + [cube[49],cube[48],cube[47],cube[46],cube[45],cube[44],cube[43],cube[42],cube[41],cube[40],cube[39],cube[38],cube[37],cube[36],cube[35],cube[34],cube[33],cube[32]] + cube[50:53] + [cube[28]] + cube[54:57] + [cube[24]] + cube[58:61] + [cube[20]] + cube[62:81] + [cube[16],cube[15],cube[14],cube[13]] + cube[85:97]

def rotate_444_Fw(cube):
    return cube[0:9] + [cube[31],cube[27],cube[23],cube[19],cube[32],cube[28],cube[24],cube[20]] + cube[17:19] + [cube[85],cube[81]] + cube[21:23] + [cube[86],cube[82]] + cube[25:27] + [cube[87],cube[83]] + cube[29:31] + [cube[88],cube[84],cube[45],cube[41],cube[37],cube[33],cube[46],cube[42],cube[38],cube[34],cube[47],cube[43],cube[39],cube[35],cube[48],cube[44],cube[40],cube[36],cube[13],cube[9]] + cube[51:53] + [cube[14],cube[10]] + cube[55:57] + [cube[15],cube[11]] + cube[59:61] + [cube[16],cube[12]] + cube[63:81] + [cube[61],cube[57],cube[53],cube[49],cube[62],cube[58],cube[54],cube[50]] + cube[89:97]

def rotate_444_Fw_prime(cube):
    return cube[0:9] + [cube[50],cube[54],cube[58],cube[62],cube[49],cube[53],cube[57],cube[61]] + cube[17:19] + [cube[12],cube[16]] + cube[21:23] + [cube[11],cube[15]] + cube[25:27] + [cube[10],cube[14]] + cube[29:31] + [cube[9],cube[13],cube[36],cube[40],cube[44],cube[48],cube[35],cube[39],cube[43],cube[47],cube[34],cube[38],cube[42],cube[46],cube[33],cube[37],cube[41],cube[45],cube[84],cube[88]] + cube[51:53] + [cube[83],cube[87]] + cube[55:57] + [cube[82],cube[86]] + cube[59:61] + [cube[81],cube[85]] + cube[63:81] + [cube[20],cube[24],cube[28],cube[32],cube[19],cube[23],cube[27],cube[31]] + cube[89:97]

def rotate_444_Fw2(cube):
    return cube[0:9] + [cube[88],cube[87],cube[86],cube[85],cube[84],cube[83],cube[82],cube[81]] + cube[17:19] + [cube[62],cube[61]] + cube[21:23] + [cube[58],cube[57]] + cube[25:27] + [cube[54],cube[53]] + cube[29:31] + [cube[50],cube[49],cube[48],cube[47],cube[46],cube[45],cube[44],cube[43],cube[42],cube[41],cube[40],cube[39],cube[38],cube[37],cube[36],cube[35],cube[34],cube[33],cube[32],cube[31]] + cube[51:53] + [cube[28],cube[27]] + cube[55:57] + [cube[24],cube[23]] + cube[59:61] + [cube[20],cube[19]] + cube[63:81] + [cube[16],cube[15],cube[14],cube[13],cube[12],cube[11],cube[10],cube[9]] + cube[89:97]

def rotate_444_R(cube):
    return cube[0:4] + [cube[36]] + cube[5:8] + [cube[40]] + cube[9:12] + [cube[44]] + cube[13:16] + [cube[48]] + cube[17:36] + [cube[84]] + cube[37:40] + [cube[88]] + cube[41:44] + [cube[92]] + cube[45:48] + [cube[96],cube[61],cube[57],cube[53],cube[49],cube[62],cube[58],cube[54],cube[50],cube[63],cube[59],cube[55],cube[51],cube[64],cube[60],cube[56],cube[52],cube[16]] + cube[66:69] + [cube[12]] + cube[70:73] + [cube[8]] + cube[74:77] + [cube[4]] + cube[78:84] + [cube[77]] + cube[85:88] + [cube[73]] + cube[89:92] + [cube[69]] + cube[93:96] + [cube[65]]

def rotate_444_R_prime(cube):
    return cube[0:4] + [cube[77]] + cube[5:8] + [cube[73]] + cube[9:12] + [cube[69]] + cube[13:16] + [cube[65]] + cube[17:36] + [cube[4]] + cube[37:40] + [cube[8]] + cube[41:44] + [cube[12]] + cube[45:48] + [cube[16],cube[52],cube[56],cube[60],cube[64],cube[51],cube[55],cube[59],cube[63],cube[50],cube[54],cube[58],cube[62],cube[49],cube[53],cube[57],cube[61],cube[96]] + cube[66:69] + [cube[92]] + cube[70:73] + [cube[88]] + cube[74:77] + [cube[84]] + cube[78:84] + [cube[36]] + cube[85:88] + [cube[40]] + cube[89:92] + [cube[44]] + cube[93:96] + [cube[48]]

def rotate_444_R2(cube):
    return cube[0:4] + [cube[84]] + cube[5:8] + [cube[88]] + cube[9:12] + [cube[92]] + cube[13:16] + [cube[96]] + cube[17:36] + [cube[77]] + cube[37:40] + [cube[73]] + cube[41:44] + [cube[69]] + cube[45:48] + [cube[65],cube[64],cube[63],cube[62],cube[61],cube[60],cube[59],cube[58],cube[57],cube[56],cube[55],cube[54],cube[53],cube[52],cube[51],cube[50],cube[49],cube[48]] + cube[66:69] + [cube[44]] + cube[70:73] + [cube[40]] + cube[74:77] + [cube[36]] + cube[78:84] + [cube[4]] + cube[85:88] + [cube[8]] + cube[89:92] + [cube[12]] + cube[93:96] + [cube[16]]

def rotate_444_Rw(cube):
    return cube[0:3] + cube[35:37] + cube[5:7] + cube[39:41] + cube[9:11] + cube[43:45] + cube[13:15] + cube[47:49] + cube[17:35] + cube[83:85] + cube[37:39] + cube[87:89] + cube[41:43] + cube[91:93] + cube[45:47] + cube[95:97] + [cube[61],cube[57],cube[53],cube[49],cube[62],cube[58],cube[54],cube[50],cube[63],cube[59],cube[55],cube[51],cube[64],cube[60],cube[56],cube[52],cube[16],cube[15]] + cube[67:69] + [cube[12],cube[11]] + cube[71:73] + [cube[8],cube[7]] + cube[75:77] + [cube[4],cube[3]] + cube[79:83] + [cube[78],cube[77]] + cube[85:87] + [cube[74],cube[73]] + cube[89:91] + [cube[70],cube[69]] + cube[93:95] + [cube[66],cube[65]]

def rotate_444_Rw_prime(cube):
    return cube[0:3] + [cube[78],cube[77]] + cube[5:7] + [cube[74],cube[73]] + cube[9:11] + [cube[70],cube[69]] + cube[13:15] + [cube[66],cube[65]] + cube[17:35] + cube[3:5] + cube[37:39] + cube[7:9] + cube[41:43] + cube[11:13] + cube[45:47] + cube[15:17] + [cube[52],cube[56],cube[60],cube[64],cube[51],cube[55],cube[59],cube[63],cube[50],cube[54],cube[58],cube[62],cube[49],cube[53],cube[57],cube[61],cube[96],cube[95]] + cube[67:69] + [cube[92],cube[91]] + cube[71:73] + [cube[88],cube[87]] + cube[75:77] + [cube[84],cube[83]] + cube[79:83] + cube[35:37] + cube[85:87] + cube[39:41] + cube[89:91] + cube[43:45] + cube[93:95] + cube[47:49]

def rotate_444_Rw2(cube):
    return cube[0:3] + cube[83:85] + cube[5:7] + cube[87:89] + cube[9:11] + cube[91:93] + cube[13:15] + cube[95:97] + cube[17:35] + [cube[78],cube[77]] + cube[37:39] + [cube[74],cube[73]] + cube[41:43] + [cube[70],cube[69]] + cube[45:47] + [cube[66],cube[65],cube[64],cube[63],cube[62],cube[61],cube[60],cube[59],cube[58],cube[57],cube[56],cube[55],cube[54],cube[53],cube[52],cube[51],cube[50],cube[49],cube[48],cube[47]] + cube[67:69] + [cube[44],cube[43]] + cube[71:73] + [cube[40],cube[39]] + cube[75:77] + [cube[36],cube[35]] + cube[79:83] + cube[3:5] + cube[85:87] + cube[7:9] + cube[89:91] + cube[11:13] + cube[93:95] + cube[15:17]

def rotate_444_B(cube):
    return [cube[0],cube[52],cube[56],cube[60],cube[64]] + cube[5:17] + [cube[4]] + cube[18:21] + [cube[3]] + cube[22:25] + [cube[2]] + cube[26:29] + [cube[1]] + cube[30:52] + [cube[96]] + cube[53:56] + [cube[95]] + cube[57:60] + [cube[94]] + cube[61:64] + [cube[93],cube[77],cube[73],cube[69],cube[65],cube[78],cube[74],cube[70],cube[66],cube[79],cube[75],cube[71],cube[67],cube[80],cube[76],cube[72],cube[68]] + cube[81:93] + [cube[17],cube[21],cube[25],cube[29]]

def rotate_444_B_prime(cube):
    return [cube[0],cube[29],cube[25],cube[21],cube[17]] + cube[5:17] + [cube[93]] + cube[18:21] + [cube[94]] + cube[22:25] + [cube[95]] + cube[26:29] + [cube[96]] + cube[30:52] + [cube[1]] + cube[53:56] + [cube[2]] + cube[57:60] + [cube[3]] + cube[61:64] + [cube[4],cube[68],cube[72],cube[76],cube[80],cube[67],cube[71],cube[75],cube[79],cube[66],cube[70],cube[74],cube[78],cube[65],cube[69],cube[73],cube[77]] + cube[81:93] + [cube[64],cube[60],cube[56],cube[52]]

def rotate_444_B2(cube):
    return [cube[0],cube[96],cube[95],cube[94],cube[93]] + cube[5:17] + [cube[64]] + cube[18:21] + [cube[60]] + cube[22:25] + [cube[56]] + cube[26:29] + [cube[52]] + cube[30:52] + [cube[29]] + cube[53:56] + [cube[25]] + cube[57:60] + [cube[21]] + cube[61:64] + [cube[17],cube[80],cube[79],cube[78],cube[77],cube[76],cube[75],cube[74],cube[73],cube[72],cube[71],cube[70],cube[69],cube[68],cube[67],cube[66],cube[65]] + cube[81:93] + [cube[4],cube[3],cube[2],cube[1]]

def rotate_444_Bw(cube):
    return [cube[0],cube[52],cube[56],cube[60],cube[64],cube[51],cube[55],cube[59],cube[63]] + cube[9:17] + [cube[4],cube[8]] + cube[19:21] + [cube[3],cube[7]] + cube[23:25] + [cube[2],cube[6]] + cube[27:29] + [cube[1],cube[5]] + cube[31:51] + [cube[92],cube[96]] + cube[53:55] + [cube[91],cube[95]] + cube[57:59] + [cube[90],cube[94]] + cube[61:63] + [cube[89],cube[93],cube[77],cube[73],cube[69],cube[65],cube[78],cube[74],cube[70],cube[66],cube[79],cube[75],cube[71],cube[67],cube[80],cube[76],cube[72],cube[68]] + cube[81:89] + [cube[18],cube[22],cube[26],cube[30],cube[17],cube[21],cube[25],cube[29]]

def rotate_444_Bw_prime(cube):
    return [cube[0],cube[29],cube[25],cube[21],cube[17],cube[30],cube[26],cube[22],cube[18]] + cube[9:17] + [cube[93],cube[89]] + cube[19:21] + [cube[94],cube[90]] + cube[23:25] + [cube[95],cube[91]] + cube[27:29] + [cube[96],cube[92]] + cube[31:51] + [cube[5],cube[1]] + cube[53:55] + [cube[6],cube[2]] + cube[57:59] + [cube[7],cube[3]] + cube[61:63] + [cube[8],cube[4],cube[68],cube[72],cube[76],cube[80],cube[67],cube[71],cube[75],cube[79],cube[66],cube[70],cube[74],cube[78],cube[65],cube[69],cube[73],cube[77]] + cube[81:89] + [cube[63],cube[59],cube[55],cube[51],cube[64],cube[60],cube[56],cube[52]]

def rotate_444_Bw2(cube):
    return [cube[0],cube[96],cube[95],cube[94],cube[93],cube[92],cube[91],cube[90],cube[89]] + cube[9:17] + [cube[64],cube[63]] + cube[19:21] + [cube[60],cube[59]] + cube[23:25] + [cube[56],cube[55]] + cube[27:29] + [cube[52],cube[51]] + cube[31:51] + [cube[30],cube[29]] + cube[53:55] + [cube[26],cube[25]] + cube[57:59] + [cube[22],cube[21]] + cube[61:63] + [cube[18],cube[17],cube[80],cube[79],cube[78],cube[77],cube[76],cube[75],cube[74],cube[73],cube[72],cube[71],cube[70],cube[69],cube[68],cube[67],cube[66],cube[65]] + cube[81:89] + [cube[8],cube[7],cube[6],cube[5],cube[4],cube[3],cube[2],cube[1]]

def rotate_444_D(cube):
    return cube[0:29] + cube[77:81] + cube[33:45] + cube[29:33] + cube[49:61] + cube[45:49] + cube[65:77] + cube[61:65] + [cube[93],cube[89],cube[85],cube[81],cube[94],cube[90],cube[86],cube[82],cube[95],cube[91],cube[87],cube[83],cube[96],cube[92],cube[88],cube[84]]

def rotate_444_D_prime(cube):
    return cube[0:29] + cube[45:49] + cube[33:45] + cube[61:65] + cube[49:61] + cube[77:81] + cube[65:77] + cube[29:33] + [cube[84],cube[88],cube[92],cube[96],cube[83],cube[87],cube[91],cube[95],cube[82],cube[86],cube[90],cube[94],cube[81],cube[85],cube[89],cube[93]]

def rotate_444_D2(cube):
    return cube[0:29] + cube[61:65] + cube[33:45] + cube[77:81] + cube[49:61] + cube[29:33] + cube[65:77] + cube[45:49] + [cube[96],cube[95],cube[94],cube[93],cube[92],cube[91],cube[90],cube[89],cube[88],cube[87],cube[86],cube[85],cube[84],cube[83],cube[82],cube[81]]

def rotate_444_Dw(cube):
    return cube[0:25] + cube[73:81] + cube[33:41] + cube[25:33] + cube[49:57] + cube[41:49] + cube[65:73] + cube[57:65] + [cube[93],cube[89],cube[85],cube[81],cube[94],cube[90],cube[86],cube[82],cube[95],cube[91],cube[87],cube[83],cube[96],cube[92],cube[88],cube[84]]

def rotate_444_Dw_prime(cube):
    return cube[0:25] + cube[41:49] + cube[33:41] + cube[57:65] + cube[49:57] + cube[73:81] + cube[65:73] + cube[25:33] + [cube[84],cube[88],cube[92],cube[96],cube[83],cube[87],cube[91],cube[95],cube[82],cube[86],cube[90],cube[94],cube[81],cube[85],cube[89],cube[93]]

def rotate_444_Dw2(cube):
    return cube[0:25] + cube[57:65] + cube[33:41] + cube[73:81] + cube[49:57] + cube[25:33] + cube[65:73] + cube[41:49] + [cube[96],cube[95],cube[94],cube[93],cube[92],cube[91],cube[90],cube[89],cube[88],cube[87],cube[86],cube[85],cube[84],cube[83],cube[82],cube[81]]

def rotate_444_x(cube):
    return [cube[0]] + cube[33:49] + [cube[20],cube[24],cube[28],cube[32],cube[19],cube[23],cube[27],cube[31],cube[18],cube[22],cube[26],cube[30],cube[17],cube[21],cube[25],cube[29]] + cube[81:97] + [cube[61],cube[57],cube[53],cube[49],cube[62],cube[58],cube[54],cube[50],cube[63],cube[59],cube[55],cube[51],cube[64],cube[60],cube[56],cube[52],cube[16],cube[15],cube[14],cube[13],cube[12],cube[11],cube[10],cube[9],cube[8],cube[7],cube[6],cube[5],cube[4],cube[3],cube[2],cube[1],cube[80],cube[79],cube[78],cube[77],cube[76],cube[75],cube[74],cube[73],cube[72],cube[71],cube[70],cube[69],cube[68],cube[67],cube[66],cube[65]]

def rotate_444_x_prime(cube):
    return [cube[0],cube[80],cube[79],cube[78],cube[77],cube[76],cube[75],cube[74],cube[73],cube[72],cube[71],cube[70],cube[69],cube[68],cube[67],cube[66],cube[65],cube[29],cube[25],cube[21],cube[17],cube[30],cube[26],cube[22],cube[18],cube[31],cube[27],cube[23],cube[19],cube[32],cube[28],cube[24],cube[20]] + cube[1:17] + [cube[52],cube[56],cube[60],cube[64],cube[51],cube[55],cube[59],cube[63],cube[50],cube[54],cube[58],cube[62],cube[49],cube[53],cube[57],cube[61],cube[96],cube[95],cube[94],cube[93],cube[92],cube[91],cube[90],cube[89],cube[88],cube[87],cube[86],cube[85],cube[84],cube[83],cube[82],cube[81]] + cube[33:49]

def rotate_444_y(cube):
    return [cube[0],cube[13],cube[9],cube[5],cube[1],cube[14],cube[10],cube[6],cube[2],cube[15],cube[11],cube[7],cube[3],cube[16],cube[12],cube[8],cube[4]] + cube[33:81] + cube[17:33] + [cube[84],cube[88],cube[92],cube[96],cube[83],cube[87],cube[91],cube[95],cube[82],cube[86],cube[90],cube[94],cube[81],cube[85],cube[89],cube[93]]

def rotate_444_y_prime(cube):
    return [cube[0],cube[4],cube[8],cube[12],cube[16],cube[3],cube[7],cube[11],cube[15],cube[2],cube[6],cube[10],cube[14],cube[1],cube[5],cube[9],cube[13]] + cube[65:81] + cube[17:65] + [cube[93],cube[89],cube[85],cube[81],cube[94],cube[90],cube[86],cube[82],cube[95],cube[91],cube[87],cube[83],cube[96],cube[92],cube[88],cube[84]]

def rotate_444_z(cube):
    return [cube[0],cube[29],cube[25],cube[21],cube[17],cube[30],cube[26],cube[22],cube[18],cube[31],cube[27],cube[23],cube[19],cube[32],cube[28],cube[24],cube[20],cube[93],cube[89],cube[85],cube[81],cube[94],cube[90],cube[86],cube[82],cube[95],cube[91],cube[87],cube[83],cube[96],cube[92],cube[88],cube[84],cube[45],cube[41],cube[37],cube[33],cube[46],cube[42],cube[38],cube[34],cube[47],cube[43],cube[39],cube[35],cube[48],cube[44],cube[40],cube[36],cube[13],cube[9],cube[5],cube[1],cube[14],cube[10],cube[6],cube[2],cube[15],cube[11],cube[7],cube[3],cube[16],cube[12],cube[8],cube[4],cube[68],cube[72],cube[76],cube[80],cube[67],cube[71],cube[75],cube[79],cube[66],cube[70],cube[74],cube[78],cube[65],cube[69],cube[73],cube[77],cube[61],cube[57],cube[53],cube[49],cube[62],cube[58],cube[54],cube[50],cube[63],cube[59],cube[55],cube[51],cube[64],cube[60],cube[56],cube[52]]

def rotate_444_z_prime(cube):
    return [cube[0],cube[52],cube[56],cube[60],cube[64],cube[51],cube[55],cube[59],cube[63],cube[50],cube[54],cube[58],cube[62],cube[49],cube[53],cube[57],cube[61],cube[4],cube[8],cube[12],cube[16],cube[3],cube[7],cube[11],cube[15],cube[2],cube[6],cube[10],cube[14],cube[1],cube[5],cube[9],cube[13],cube[36],cube[40],cube[44],cube[48],cube[35],cube[39],cube[43],cube[47],cube[34],cube[38],cube[42],cube[46],cube[33],cube[37],cube[41],cube[45],cube[84],cube[88],cube[92],cube[96],cube[83],cube[87],cube[91],cube[95],cube[82],cube[86],cube[90],cube[94],cube[81],cube[85],cube[89],cube[93],cube[77],cube[73],cube[69],cube[65],cube[78],cube[74],cube[70],cube[66],cube[79],cube[75],cube[71],cube[67],cube[80],cube[76],cube[72],cube[68],cube[20],cube[24],cube[28],cube[32],cube[19],cube[23],cube[27],cube[31],cube[18],cube[22],cube[26],cube[30],cube[17],cube[21],cube[25],cube[29]]

rotate_mapper_444 = {
    "B" : rotate_444_B,
    "B'" : rotate_444_B_prime,
    "B2" : rotate_444_B2,
    "Bw" : rotate_444_Bw,
    "Bw'" : rotate_444_Bw_prime,
    "Bw2" : rotate_444_Bw2,
    "D" : rotate_444_D,
    "D'" : rotate_444_D_prime,
    "D2" : rotate_444_D2,
    "Dw" : rotate_444_Dw,
    "Dw'" : rotate_444_Dw_prime,
    "Dw2" : rotate_444_Dw2,
    "F" : rotate_444_F,
    "F'" : rotate_444_F_prime,
    "F2" : rotate_444_F2,
    "Fw" : rotate_444_Fw,
    "Fw'" : rotate_444_Fw_prime,
    "Fw2" : rotate_444_Fw2,
    "L" : rotate_444_L,
    "L'" : rotate_444_L_prime,
    "L2" : rotate_444_L2,
    "Lw" : rotate_444_Lw,
    "Lw'" : rotate_444_Lw_prime,
    "Lw2" : rotate_444_Lw2,
    "R" : rotate_444_R,
    "R'" : rotate_444_R_prime,
    "R2" : rotate_444_R2,
    "Rw" : rotate_444_Rw,
    "Rw'" : rotate_444_Rw_prime,
    "Rw2" : rotate_444_Rw2,
    "U" : rotate_444_U,
    "U'" : rotate_444_U_prime,
    "U2" : rotate_444_U2,
    "Uw" : rotate_444_Uw,
    "Uw'" : rotate_444_Uw_prime,
    "Uw2" : rotate_444_Uw2,
    "x" : rotate_444_x,
    "x'" : rotate_444_x_prime,
    "y" : rotate_444_y,
    "y'" : rotate_444_y_prime,
    "z" : rotate_444_z,
    "z'" : rotate_444_z_prime,
}

def rotate_444(cube, step):
    return rotate_mapper_444[step](cube)


if __name__ == '__main__':
    import doctest

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(filename)16s %(levelname)8s: %(message)s')
    log = logging.getLogger(__name__)

    # Color the errors and warnings in red
    logging.addLevelName(logging.ERROR, "\033[91m   %s\033[0m" % logging.getLevelName(logging.ERROR))
    logging.addLevelName(logging.WARNING, "\033[91m %s\033[0m" % logging.getLevelName(logging.WARNING))

    doctest.testmod()
