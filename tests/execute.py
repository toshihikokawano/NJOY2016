#!/usr/bin/env python

import filecmp
import glob
import os
import re
import subprocess


floatPattern = re.compile("""(
                                (
                                    [-+]?				# sign (optional)
                                    \d+					# digit(s)
                                )
                                (
                                    \.              # period
                                    \d+  		    # digit(s)
                                )?                  # period+digits  (optional)
                                (
                                    ([eE])?			# designation (optional)
                                    [-+]			# sign (required)
                                    \d+				# digit(s) (required)
                                )? 					# exponent (optional)
                            )
                          """, re.VERBOSE)


def identicalLines(refLines, trialLines, diffFile,
                   relativeError=1E-8, absoluteError=1E-8):
    """
    Look at two lists of strings (presumably lines from two files) and compare
    them; that is, determine if they are the same within the given tolerance.
    Returns True if everything is the same, returns False if anythin differs.
    """
    if len(refLines) != len(trialLines):
        print("Reference file and trial file have different number of lines!")
        return False

    equivalent = True
    for n, (ref, trial) in enumerate(zip(refLines, trialLines)):
        if ref != trial:

            # Look for numbers
            refFloats = floatPattern.findall(ref)
            if refFloats:
                floatEquivalence = True
                trialFloats = floatPattern.findall(trial)

                if len(refFloats) != len(trialFloats):
                    print("Found wrong number of floats on line: {}".format(n))
                    floatEquivalence = False
                else:
                    # Look at all the floats on the lines
                    for rF, tF in zip(refFloats, trialFloats):
                        equal = fuzzyDiff(makeFloat(rF), makeFloat(tF),
                                          relativeError, absoluteError)
                        if not equal:
                            print("{} and {} are not equal".format(
                                rF[0], tF[0]))
                            floatEquivalence = False

                if not floatEquivalence:
                    equivalent = False
                    writeDiff(diffFile, ref, trial, n)

            # Lines contain only text (no numbers)
            else:
                equivalent = False
                writeDiff(diffFile, ref, trial, n)

        # Lines are the the same
        else:
            continue

    return equivalent


def makeFloat(D):
    """
    """
    try:
        return float(D[0])
    except (TypeError, ValueError):
        if not D[-1]:
            d = "{}{}E{}".format(D[1], D[2], D[3])
            f = float(d)
            return f


def writeDiff(diff_file, refLine, trialLine, lineNumber):
    """
    Write the differences to the diff file.
    """
    diff_file.write("***************\n")
    diff_file.write("*** {} ***\n".format(lineNumber+1))
    diff_file.write("!{}".format(refLine))
    diff_file.write("--- {} ---\n".format(lineNumber+1))
    diff_file.write("!{}".format(trialLine))


def fuzzyDiff(a, b, relativeError=1E-6, absoluteError=1E-8):
    """
    fuzzDiff will compare to numbers (a and b) to see if they are identical
    within the given tolerance. Returns bool.
    """
    diff = a - b
    delta = max(abs(a), abs(b))*relativeError + absoluteError
    return (diff <= abs(delta))


retained_tapes = set(glob.glob('tape*'))
reference_tapes = glob.glob('referenceTape*')

with open('input', 'r') as i, \
     open('output', 'w') as o, \
     open('error', 'w') as e:
    njoy = os.path.join('..', '..', 'njoy')
    child = subprocess.Popen(njoy, stdin=i, stdout=o, stderr=e)
    child.communicate()
    if (child.poll()):
        print("Error enountered while running NJOY!")
        exit(child.poll())

    for reference_tape in reference_tapes:
        trial_tape = 'tape' + reference_tape[-2:]
        if not filecmp.cmp(reference_tape, trial_tape):
            with open(reference_tape, 'r') as reference_file, \
                 open(trial_tape, 'r') as trial_file, \
                 open(trial_tape + '_diff', 'w') as diff_file:
                should_exit = False
                reference_lines = reference_file.readlines()
                trial_lines = trial_file.readlines()
                reference_lines = [re.sub(r'\d{2}/\d{2}/\d{2}',
                                          r'XX/XX/XX', line)
                                   for line in reference_lines]
                trial_lines = [re.sub(r'\d{2}/\d{2}/\d{2}',
                                      r'XX/XX/XX', line)
                               for line in trial_lines]

                diff_file.write("*** {} ***\n".format(reference_tape))
                diff_file.write("--- {} ---\n".format(trial_tape))

                identical = identicalLines(
                    reference_lines, trial_lines, diff_file, 1E-9, 1E-10)
                should_exit = not identical

            if should_exit:
                exit(99)

    removed_tapes = list(set(glob.glob('tape*')) - retained_tapes)
    for tape in removed_tapes:
        os.remove(tape)

    for diff in glob.glob('*_diff'):
        os.remove(diff)

os.remove('output')
os.remove('error')
