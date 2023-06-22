# some parts co-opted from Spleenface

import random
import tqdm
from collections import Counter

landsInLib = 0
libSize = 0

# Hyperparameters
# The ratio of (lands in lib / library size) where shuffling at the second shuffler is better than continuing to mill past
land_lib_ratio = 0.1
# The number of sims to use to generate each number
sim_count = 10000


def dredge(amt, lib):
    trig = 0
    found = []
    for i in range(amt):  # take the first X out of the library
        card = lib.pop(0)
        if card == "dakmor":  # found dakmor
            found.append('dakmor')

        elif card == "land":  # found a land
            trig = 1

        elif card == 'loam':
            found.append('loam')

        elif card == 'shuffler':
            found.append('shuffler')

    return lib, trig, found


def createLib(lands, size):
    lib = []  # empty library
    for i in range(lands):  # add the requisite number of lands
        lib.append("land")
    lib.append("dakmor")  # add dakmor
    lib.append("shuffler")  # add 2 shufflers
    lib.append("shuffler")
    lib.append("loam")
    # number of cards in library - number of lands - 4 for dakmor, 2 shufflers, and loam
    for j in range(size - lands - 4):
        lib.append("nonland")
    return lib


# Accepts a shuffled array representing the library, and the number of triggers we can generate
def handle_dredge(lib, trigs):
    global landsInLib
    global libSize
    starting_trigs = trigs
    found_loam = False
    first_shuffler_found = False
    second_shuffler_found = False

    while trigs > 0:  # while you still have a draw trigger
        trigs -= 1  # remove a trigger for dredging

        if trigs < starting_trigs:
            starting_trigs -= 1
            landsInLib += 1
            libSize += 1

        lib, trig, found = dredge(6, lib)

        if 'dakmor' in found:
            return 0

        elif 'loam' in found:
            found_loam = True

        trigs += trig  # add a trigger if we hit a land

        if 'shuffler' in found and not first_shuffler_found:
            first_shuffler_found = True

        if 'shuffler' in found and first_shuffler_found:
            second_shuffler_found = True

        # TODO Vary the ratio and see how percentages are impacted
        if 'shuffler' in found and first_shuffler_found and lib.count('land') / len(lib) < land_lib_ratio:
            found_loam = False
            first_shuffler_found = False
            lib = createLib(landsInLib, libSize)
            random.shuffle(lib)
            continue

        if len(lib) == 6 or len(lib) == 7:
            found_loam = False
            first_shuffler_found = False

            # If we hit a land off the last mill, draw one.
            if trig > 0:
                trigs -= 1
                card = lib.pop(0)
                if card == 'dakmor':
                    return 0
                elif card == 'land':
                    trigs += 1
                    starting_trigs += 1
                    landsInLib -= 1
                    libSize -= 1
                elif card == 'nonland':
                    libSize -= 1
                elif card == 'loam':
                    found_loam = True
                    libSize -= 1
                # TODO Account for drawing a shuffler here (modify how createLib works)

            lib = createLib(landsInLib, libSize)
            random.shuffle(lib)
            continue

        # got through whole library
        if len(lib) < 6:

            # If we have enough draw triggers to draw the remaining cards, do so
            if trigs >= len(lib):
                return 0

            # If we're out of triggers, gg
            elif trigs == 0:
                return 11

            # This is the only case where you would dredge loam
            elif trigs > 0 and len(lib) == 5 and found_loam and not second_shuffler_found:
                trigs -= 1
                lib, trig, found = dredge(3, lib)  # Dredge Loam

                trigs += trig

                instances_of_shuffler = 0
                for item in found:
                    if item == 'shuffler':
                        instances_of_shuffler += 1

                # There is a shuffler in the next 2 cards
                if 'dakmor' in found and instances_of_shuffler != 2 and not first_shuffler_found:
                    return 0

                # If there is a land in the last 2, we cannot take dakmor or we mill ourselves
                elif 'dakmor' in found and instances_of_shuffler == 2:
                    if 'land' in lib:
                        # If we still have draw triggers, we can resolve one, shuffle up, and go back to dredging ggt
                        if trigs > 0:
                            trigs -= 1
                            card = lib.pop(0)
                            if card == 'land':
                                trigs += 1
                                starting_trigs += 1
                                landsInLib -= 1
                                libSize -= 1
                            elif card == 'nonland':
                                libSize -= 1

                            if trigs == 0:
                                return 1
                            else:
                                found_loam = False
                                first_shuffler_found = False
                                lib = createLib(landsInLib, libSize)
                                random.shuffle(lib)
                                continue
                        else:
                            return 1
                    else:
                        return 0

                # Dakmor is in the last two, risk it for the draw
                elif instances_of_shuffler > 0 and trigs > 0:
                    if trigs >= 2:
                        return 0
                    trigs -= 1
                    card = lib.pop(0)
                    if card == 'dakmor':  # GGEZ wasn't even close btw #calculated
                        return 0
                    elif card == 'land':  # Found new fodder to discard
                        return 0
                    return 2  # Out of draws

                # The last shuffler and dakmor are the last 2 cards, and we have enough draw triggers to get them both
                elif instances_of_shuffler == 0 and trigs >= 2:
                    return 0

                # The last shuffler and dakmor are the last 2 cards, risk it for the draw
                elif instances_of_shuffler == 0 and trigs == 1:
                    trigs -= 1
                    card = lib.pop(0)
                    if card == 'dakmor':  # GGEZ wasn't even close btw #calculated
                        return 0
                    return 3  # Out of draws

                # The last shuffler and dakmor are the last 2 cards, but there's nothing we can do
                elif instances_of_shuffler == 0 and trigs == 0:
                    return 4  # Out of draws

                # Out of draws
                else:
                    return 12

            elif trigs > 0 and len(lib) == 5 and found_loam and second_shuffler_found:
                trigs -= 1
                lib, trig, found = dredge(3, lib)  # Dredge Loam

                trigs += trig

                # If we milled dakmor | there is a land in the last 2 cards in lib, we cannot take dakmor
                if 'dakmor' in found:
                    if 'land' in lib:
                        # If we still have draw triggers, we can resolve one, shuffle up, and go back to dredging ggt
                        if trigs > 0:
                            trigs -= 1
                            card = lib.pop(0)
                            if card == 'land':
                                trigs += 1
                                starting_trigs += 1
                                landsInLib -= 1
                                libSize -= 1
                            elif card == 'nonland':
                                libSize -= 1

                            if trigs == 0:
                                return 5
                            else:
                                found_loam = False
                                first_shuffler_found = False
                                lib = createLib(landsInLib, libSize)
                                random.shuffle(lib)
                                continue
                        else:
                            return 5
                    else:
                        return 0

                # We did not mill dakmor | it is in the last 2 cards, we can try to draw it
                elif trigs > 0:
                    # We have enough draw triggers to draw both
                    if trigs >= 2:
                        return 0

                    # Forced to draw, trig = 1 implies trigs = 1 here
                    elif trig == 1:
                        trigs -= 1
                        card = lib.pop(0)
                        if card == 'dakmor':
                            return 0
                        elif card == 'land':
                            return 0
                        elif card == 'nonland':
                            return 9

                    # TODO determine if the odds are better to just shuffle up instead of drawing
                    elif trigs == 1:
                        trigs -= 1
                        card = lib.pop(0)
                        if card == 'dakmor':
                            return 0
                        elif card == 'land':
                            return 0
                        elif card == 'nonland':
                            return 9

                    # no draws left, gg
                    else:
                        return 9

                # We do not have any more draw triggers
                else:
                    return 8

            # If we've already passed a shuffler, we can resolve remining draws on the stack and shuffle up and go back to ggt
            elif first_shuffler_found:
                found_loam = False
                first_shuffler_found = False

                # If we hit a land off the last mill, we must draw one to continue.
                if trig > 0:
                    trigs -= 1
                    card = lib.pop(0)
                    if card == 'dakmor':
                        return 0
                    elif card == 'land':
                        trigs += 1
                        starting_trigs += 1
                        landsInLib -= 1
                        libSize -= 1
                    elif card == 'nonland':
                        libSize -= 1
                    elif card == 'loam':
                        found_loam = True
                        libSize -= 1
                    # TODO Account for drawing a shuffler here (modify how createLib works)

                lib = createLib(landsInLib, libSize)
                random.shuffle(lib)
                continue

            # If we have triggers but either no loam or the library is too small, and both shufflers are in the remaining cards, we have no option but to draw
            elif trigs > 0:
                while trigs > 0:
                    trigs -= 1

                    card = lib.pop(0)
                    if card == 'dakmor':  # GGEZ wasn't even close btw #calculated
                        return 0
                    elif card == 'land':  # Found new fodder to discard
                        trigs += 1
                    # If hit shuffler or nonland, do nothing
                return 6  # Out of draws

    return 7  # failed


# Accepts a number of lands in the library, size of the library, and number of triggers we can generate
def sim(trigs, originalLibSize, originalLandCount):
    global landsInLib
    global libSize
    succ = 0
    fails = []

    # Creates the library as a shuffled array containing 'l' for land, 'd' for dakmor, and 'n' for nonland
    lib = createLib(landsInLib, libSize)

    # Run the simulation x times
    for i in range(sim_count):
        libSize = originalLibSize
        landsInLib = originalLandCount

        random.shuffle(lib)

        # Sum the number of times the sim hit dakmor
        result = handle_dredge(lib.copy(), trigs)

        if result == 0:
            succ += 1
        else:
            fails.append(result)

    # Return the success rate as a percentage
    return succ / (sim_count / 100), fails


# Accepts a range of lands remaining in the deck, number of draw triggers we can generate separately, and library size
def ggt(minLands, maxLands, minTriggers, maxTriggers, librarySize):
    global landsInLib
    global libSize
    result = []
    fails = []
    libSize = librarySize

    # for numLands in tqdm.tqdm(range(minLands, maxLands)):
    for numLands in range(minLands, maxLands):

        # Used to display the "numLands: "
        result.append([str(numLands) + ":  "])

        # We can restart the dredging with draw triggers we generate, if we hit no lands on a mill.
        # The number of such triggers we can generate is this range.
        for triggers in range(minTriggers, maxTriggers):
            libSize = librarySize
            landsInLib = numLands

            simResult, simFails = sim(triggers, librarySize, numLands)
            fails += simFails
            result[numLands - minLands].append(simResult)

    return result, fails, (maxLands - minLands) * (maxTriggers - minTriggers) * sim_count


def display_results(results, fails, total_sim_count, minTriggers=1, maxTriggers=4):
    titleString = "Trigs:  "
    for triggers in range(minTriggers, maxTriggers):  # Create title string
        titleString = titleString + str(triggers) + "     "
    print(titleString)
    print('\n'.join(
        [' '.join([str('{:5}').format(item) for item in row]) for row in results]))

    type_counts = Counter(fails)
    labels = list(type_counts.keys())
    values = list(type_counts.values())

    for label, value in sorted(zip(labels, values)):
        print(f'Failure type: {label},\t' +
              f'Occurrences frequency: {round(value * 100 / total_sim_count, 2)}, \t' +
              f'Count (out of {total_sim_count:,}): {value:,}')


def sim_multiple_deck_sizes(minLands, maxLands, minLibrary, maxLibrary, minTriggers=1, maxTriggers=4):
    results, fails, _ = ggt(minLands, maxLands, minTriggers,
                            maxTriggers, maxLibrary)
    for i in tqdm.tqdm(range(minLibrary, maxLibrary, 1)):
        result, fail, _ = ggt(minLands, maxLands, minTriggers, maxTriggers, i)
        fails += fail
        for row_index, row in enumerate(result):
            for col_index, value in enumerate(row):
                if col_index == 0:
                    continue
                results[row_index][col_index] += value

    for row_index, row in enumerate(results):
        for k, value in enumerate(row):
            if k == 0:
                continue
            results[row_index][k] = round(
                value / (maxLibrary - minLibrary + 1), 1)

    return results, fails, (maxLibrary - minLibrary + 1) * (maxLands - minLands) * (maxTriggers - minTriggers) * sim_count


if __name__ == "__main__":
    # results, fails, total_sim_count = ggt(22, 29, 1, 4, 85)
    sim_count = 1000
    results, fails, total_sim_count = sim_multiple_deck_sizes(22, 29, 65, 85)

    display_results(results, fails, total_sim_count)
