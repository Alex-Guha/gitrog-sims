# initial ideas co-opted from Spleenface's sim
# Be warned, ye who enter: This has outgrown me and desparately needs refactoring.

from random import shuffle
from multiprocessing import Pool
from time import time
from collections import Counter

# Hyperparameters
# The ratio of (lands in library / library size) where shuffling at the second shuffler is better than continuing to mill past
land_lib_ratio = 0.1
# The number of sims to use to generate each number
sim_count = 1000
# This sets the number of cards left in library at which we shuffle if we hit a shuffler
shuffle_if_under = 7


# Milling helper function
def dredge(amount, library):
    trig = 0
    found = []
    for i in range(amount):  # take the first X out of the library
        card = library.pop(0)
        if card == "dakmor":  # found dakmor
            found.append('dakmor')

        elif card == "land":  # found a land
            trig = 1

        elif card == 'loam':
            found.append('loam')

        elif card == 'shuffler':
            found.append('shuffler')

    return library, trig, found


# Library making helper function
def createLib(lands, size):
    library = []

    # add the requisite number of lands
    for i in range(lands):
        library.append("land")

    library.append("dakmor")  # add dakmor
    library.append("shuffler")  # add 2 shufflers
    library.append("shuffler")
    library.append("loam")

    # number of cards in library - number of lands - 4 for dakmor, 2 shufflers, and loam
    for j in range(size - lands - 4):
        library.append("nonland")

    return library


# The sim
def handle_dredge(library, trigs, landsInLib, librarySize):
    # Used as a tally to add back lands when a starting trigger is used
    starting_trigs = trigs

    # Used to keep track of whether things are in the graveyard or not
    found_loam = False
    first_shuffler_found = False
    second_shuffler_found = False

    # while we still have a draw trigger
    while trigs > 0:
        trigs -= 1  # remove a trigger for dredging

        # If we used a starting trigger, add a land back to the land count and library size
        if trigs < starting_trigs:
            starting_trigs -= 1
            landsInLib += 1
            librarySize += 1

        # dredge ggt
        library, trig, found = dredge(6, library)

        # If we hit dakmor, we're set. Cases where the library would be too small to take it are handled elsewhere.
        if 'dakmor' in found:
            return (1, 0)

        # Keep track of if we have loam in the grave
        elif 'loam' in found:
            found_loam = True

        # add a trigger if we hit a land
        trigs += trig

        # If we hit the second shuffler and the library doesn't have enough lands left to sustain dredging, shuffle up and continue dredging
        # NOTE A normal player likely won't do this, so it might be worth removing
        if 'shuffler' in found and first_shuffler_found and library.count('land') / len(library) < land_lib_ratio:
            found_loam = False
            first_shuffler_found = False
            second_shuffler_found = False
            library = createLib(landsInLib, librarySize)
            shuffle(library)
            continue

        # Keep track of if the first shuffle trigger is on the stack
        if 'shuffler' in found and not first_shuffler_found:
            first_shuffler_found = True

        # Keep track of if the second shuffle trigger is on the stack
        if 'shuffler' in found and first_shuffler_found:
            second_shuffler_found = True

        # If we hit a shuffler and the library has fewer than 7 cards left, shuffle up. The odds for loaming are not good.
        if 'shuffler' in found and len(library) <= shuffle_if_under:
            found_loam = False
            first_shuffler_found = False
            second_shuffler_found = False
            library = createLib(landsInLib, librarySize)
            shuffle(library)
            continue

        # If there are 6 or 7 cards left in library, we want to shuffle up (dredging here would result in an opponent being able to force us to draw)
        if len(library) == 6 or len(library) == 7:

            # If we hit a land off the last mill, we have to consume that draw trigger before shuffling
            if trig > 0:

                # If we have loam available, dredge it
                if found_loam:
                    trigs -= 1
                    library, trig, found = dredge(3, library)  # Dredge Loam
                    librarySize -= 1

                    trigs += trig

                    # If we hit dakmor, then we're set
                    if 'dakmor' in found:
                        return (1, 1)

                    # If we hit a shuffler, great
                    elif 'shuffler' in found:
                        first_shuffler_found = False
                        second_shuffler_found = False
                        library = createLib(landsInLib, librarySize)
                        shuffle(library)
                        continue

                    # If we hit a land off loam, we must draw
                    elif trig == 1:
                        trigs -= 1
                        card = library.pop(0)
                        if card == 'dakmor':
                            return (1, 1)
                        elif card == 'land':
                            trigs += 1
                            starting_trigs += 1
                            landsInLib -= 1
                            librarySize -= 1
                        elif card == 'nonland':
                            librarySize -= 1
                        # TODO Account for drawing a shuffler here (modify how createLib works)

                # If we don't have loam, we must draw one
                else:
                    trigs -= 1
                    card = library.pop(0)
                    if card == 'dakmor':
                        return (1, 2)
                    elif card == 'land':
                        trigs += 1
                        starting_trigs += 1
                        landsInLib -= 1
                        librarySize -= 1
                    elif card == 'nonland':
                        librarySize -= 1
                    elif card == 'loam':
                        found_loam = True
                        librarySize -= 1
                    # TODO Account for drawing a shuffler here (modify how createLib works)

            if trigs == 0:
                return (0, 2)

            first_shuffler_found = False
            second_shuffler_found = False
            library = createLib(landsInLib, librarySize)
            shuffle(library)
            continue

        # XXX got through whole library
        # TODO remove any case that would result in 1 or 0 cards left in lib
        if len(library) < 6:

            # If we have enough draw triggers to draw the remaining cards, do so
            if trigs >= len(library):
                return (1, 4)

            # If we're out of triggers, gg
            elif trigs == 0:
                return (0, 4)

            # This is the only case where you would dredge loam
            elif trigs > 0 and len(library) == 5 and found_loam and not second_shuffler_found:
                trigs -= 1
                library, trig, found = dredge(3, library)  # Dredge Loam
                librarySize -= 1

                trigs += trig

                # TODO Refactor how this works, not that we are keeping track of both shufflers
                instances_of_shuffler = 0
                for item in found:
                    if item == 'shuffler':
                        instances_of_shuffler += 1

                # There is a shuffler in the next 2 cards
                if 'dakmor' in found and instances_of_shuffler != 2 and not first_shuffler_found:
                    return (1, 6)

                # If there is a land in the last 2, we cannot take dakmor or we mill ourselves
                elif 'dakmor' in found and instances_of_shuffler == 2:
                    if 'land' in library:
                        # If we still have draw triggers, we can resolve one, shuffle up, and go back to dredging ggt
                        if trigs > 0:
                            trigs -= 1
                            card = library.pop(0)
                            if card == 'land':
                                trigs += 1
                                starting_trigs += 1
                                landsInLib -= 1
                                librarySize -= 1
                            elif card == 'nonland':
                                librarySize -= 1

                            if trigs == 0:
                                return (0, 6)
                            else:
                                first_shuffler_found = False
                                second_shuffler_found = False
                                library = createLib(landsInLib, librarySize)
                                shuffle(library)
                                continue
                        else:
                            return (0, 6)
                    else:
                        return (1, 6)

                # Dakmor is in the last two, risk it for the draw
                elif instances_of_shuffler > 0 and trigs > 0:
                    if trigs >= 2:
                        return (1, 6)
                    trigs -= 1
                    card = library.pop(0)
                    if card == 'dakmor':  # GGEZ wasn't even close btw #calculated
                        return (1, 6)
                    elif card == 'land':  # Found new fodder to discard
                        return (1, 6)
                    return (0, 6)  # Out of draws

                # The last shuffler and dakmor are the last 2 cards, and we have enough draw triggers to get them both
                elif instances_of_shuffler == 0 and trigs >= 2:
                    return (1, 6)

                # The last shuffler and dakmor are the last 2 cards, risk it for the draw
                elif instances_of_shuffler == 0 and trigs == 1:
                    trigs -= 1
                    card = library.pop(0)
                    if card == 'dakmor':  # GGEZ wasn't even close btw #calculated
                        return (1, 6)
                    return (0, 6)  # Out of draws

                # The last shuffler and dakmor are the last 2 cards, but there's nothing we can do
                elif instances_of_shuffler == 0 and trigs == 0:
                    return (0, 6)  # Out of draws

                # Out of draws
                else:
                    return (0, 6)

            elif trigs > 0 and len(library) == 5 and found_loam and second_shuffler_found:
                trigs -= 1
                library, trig, found = dredge(3, library)  # Dredge Loam
                librarySize -= 1

                trigs += trig

                # If we milled dakmor | there is a land in the last 2 cards in library, we cannot take dakmor
                if 'dakmor' in found:
                    if 'land' in library:
                        # If we still have draw triggers, we can resolve one, shuffle up, and go back to dredging ggt
                        if trigs > 0:
                            trigs -= 1
                            card = library.pop(0)
                            if card == 'land':
                                trigs += 1
                                starting_trigs += 1
                                landsInLib -= 1
                                librarySize -= 1
                            elif card == 'nonland':
                                librarySize -= 1

                            if trigs == 0:
                                return (0, 7)
                            else:
                                first_shuffler_found = False
                                second_shuffler_found = False
                                library = createLib(landsInLib, librarySize)
                                shuffle(library)
                                continue
                        else:
                            return (0, 7)
                    else:
                        return (1, 7)

                # We did not mill dakmor | it is in the last 2 cards, we can try to draw it
                elif trigs > 0:
                    # We have enough draw triggers to draw both
                    if trigs >= 2:
                        return (1, 7)

                    # Forced to draw, trig = 1 implies trigs = 1 here
                    elif trig == 1:
                        trigs -= 1
                        card = library.pop(0)
                        if card == 'dakmor':
                            return (1, 7)
                        elif card == 'land':
                            return (1, 7)
                        elif card == 'nonland':
                            return (0, 7)

                    # The odds are better to shuffle up than to risk a 50/50
                    # NOTE: a normal player would not count the ratio
                    elif trigs == 1 and landsInLib / librarySize < 0.29:
                        first_shuffler_found = False
                        second_shuffler_found = False
                        library = createLib(landsInLib, librarySize)
                        shuffle(library)
                        continue

                    # The odds are better to risk the 50/50
                    elif trigs == 1:
                        trigs -= 1
                        card = library.pop(0)
                        if card == 'dakmor':
                            return (1, 7)
                        elif card == 'land':
                            return (1, 7)
                        elif card == 'nonland':
                            return (0, 7)

                    # no draws left, gg
                    else:
                        return (0, 7)

                # We do not have any more draw triggers
                else:
                    return (0, 7)

            # If we've already passed a shuffler, we can resolve remining draws on the stack and shuffle up and go back to ggt
            elif first_shuffler_found:
                found_loam = False
                first_shuffler_found = False
                second_shuffler_found = False

                # If we hit a land off the last mill, we must draw one to continue.
                if trig > 0:
                    trigs -= 1
                    card = library.pop(0)
                    if card == 'dakmor':
                        return (1, 8)
                    elif card == 'land':
                        trigs += 1
                        starting_trigs += 1
                        landsInLib -= 1
                        librarySize -= 1
                    elif card == 'nonland':
                        librarySize -= 1
                    elif card == 'loam':
                        found_loam = True
                        librarySize -= 1
                    # TODO Account for drawing a shuffler here (modify how createLib works)

                if trigs == 0:
                    return (0, 8)

                library = createLib(landsInLib, librarySize)
                shuffle(library)
                continue

            # TODO If we have triggers but either no loam or the library is too small, and both shufflers are in the remaining cards, we have no option but to draw
            elif trigs > 0:
                while trigs > 0:
                    trigs -= 1

                    card = library.pop(0)
                    if card == 'dakmor':  # GGEZ wasn't even close btw #calculated
                        return (1, 9)
                    elif card == 'land':  # Found new fodder to discard
                        trigs += 1
                    # If hit shuffler or nonland, do nothing
                return (0, 9)  # Out of draws

    return (0, 0)  # failed


# Actually runs the sims
def sim(trigs, originalLibSize, landsInLib, librarySize):
    succ = 0
    stats = []

    # Creates the library as a shuffled array containing 'l' for land, 'd' for dakmor, and 'n' for nonland
    library = createLib(landsInLib, librarySize)

    # Run the simulation x times
    for i in range(sim_count):
        shuffle(library)

        # Do the actual sim
        result = handle_dredge(library.copy(), trigs, landsInLib, librarySize)

        # Tabulate results
        succ += result[0]

        stats.append(result)

    # Return the success rate as a percentage
    return succ / (sim_count / 100), stats


# Intermediary sim
def ggt(landRatioList, minTriggers, maxTriggers, librarySize):
    result = []
    stats = []

    for i, landRatio in enumerate(landRatioList):
        numLands = round(landRatio * librarySize)

        # Used when displaying results
        result.append([f"{round(landRatio, 2)}:  "])

        # We can restart the dredging with draw triggers we generate, if we hit no lands on a mill.
        # The number of such triggers we can generate is this range.
        for triggers in range(minTriggers, maxTriggers):

            simResult, simStats = sim(
                triggers, librarySize, numLands, librarySize)

            stats += simStats
            result[i].append(simResult)

    return (result, stats, len(landRatioList) * (maxTriggers - minTriggers) * sim_count)


def display_results(results, stats, total_sim_count, landRatioList, minTriggers=1, maxTriggers=4):
    titleString = "Trigs:\t  "
    for triggers in range(minTriggers, maxTriggers):  # Create title string
        titleString = titleString + str(triggers) + "     "
    print(titleString)

    print('\n'.join(
        [' '.join([str('{:5}').format(item) for item in row]) for row in results]))
    # print('\n'.join(['\t'.join([str('{:3}').format(item) for item in row[1:]]) for row in results]))

    print(f'The first column is the (land count / library size) ratio.\n' +
          f'I.e. for the max land ratio, 85 * {round(max(landRatioList), 2)} = {round(max(landRatioList)*85)} lands ' +
          f'and 65 * {round(max(landRatioList), 2)} = {round(max(landRatioList)*65)} lands.\n' +
          f'For the min land ratio, 85 * {round(min(landRatioList), 2)} = {round(min(landRatioList)*85)} lands ' +
          f'and 65 * {round(min(landRatioList), 2)} = {round(min(landRatioList)*65)} lands.\n')

    # TODO
    stat_dict = {}
    for stat in stats:
        result = stat[0]
        location = stat[1]
        if location in stat_dict:
            stat_dict[location][result] += 1
        else:
            if result == 0:
                stat_dict[location] = [1, 0]
            else:
                stat_dict[location] = [0, 1]

    for key in sorted(stat_dict.keys()):
        print(f'Stat number: {key},\t' +
              f'Occurrence frequency: {round((stat_dict[key][0] + stat_dict[key][1]) * 100 / total_sim_count, 2)},\n\t' +
              f'Success count (out of {total_sim_count:,}): {stat_dict[key][1]:,}\n\t' +
              f'Failure count (out of {total_sim_count:,}): {stat_dict[key][0]:,}\n\t' +
              f'Success rate: {round(stat_dict[key][1]/(stat_dict[key][0] + stat_dict[key][1]), 2)}')


# Used to run a range of library sizes
def sim_multiple_deck_sizes(landRatioList, minLibrary, maxLibrary, minTriggers=1, maxTriggers=4):
    inputs = []
    for librarySize in range(minLibrary, maxLibrary + 1, 1):
        inputs.append((landRatioList, minTriggers, maxTriggers, librarySize))

    with Pool(processes=len(inputs)) as pool:
        ggt_results = pool.starmap(ggt, inputs)

    results = ggt_results[0][0]
    stats = ggt_results[0][1]

    for result in ggt_results[1:]:
        stats += result[1]
        for row_index, row in enumerate(result[0]):
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

    return results, stats, (maxLibrary - minLibrary + 1) * len(landRatioList) * (maxTriggers - minTriggers) * sim_count


if __name__ == "__main__":
    landRatioList = []

    for librarySize in range(22, 29):
        landRatioList.append(librarySize / 85)

    startTime = time()
    results, stats, total_sim_count = sim_multiple_deck_sizes(
        landRatioList, 65, 85)

    print(
        f'This is an average from a library size of 65 to 85.\nTotal number of sims: {total_sim_count:,}. Total time: {round(time() - startTime, 2)} secs.\n')
    display_results(results, stats, total_sim_count, landRatioList)
