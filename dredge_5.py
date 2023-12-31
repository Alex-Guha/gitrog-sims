# initial ideas and initial code structure co-opted from Spleenface's sim
# Be warned, ye who enter: This has outgrown me and desparately needs refactoring.

from random import shuffle
from multiprocessing import Pool
from time import time

# Hyperparameters
# The number of sims to use to generate each number (This should be set here and not changed elsewhere, for multiprocessing)
sim_count = 10000


# Milling helper function
def dredge(amount, library):
    trig = 0
    found = []
    for i in range(amount):  # take the first X out of the library
        card = library.pop(0)
        if card == "dakmor":  # found dakmor
            found.append('dakmor')
            trig = 1

        elif card == "land":  # found a land
            trig = 1

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
    library.append("shuffler")  # add shuffler
    library.append("brownscale")

    # number of cards in library - number of lands - 3 for dakmor, brownscale, and shuffler
    for j in range(size - lands - 3):
        library.append("nonland")

    return library


# The sim
def handle_dredge(library, trigs, landsInLib, librarySize):
    # Used as a tally to add back lands when a starting trigger is used
    starting_trigs = trigs

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

        # add a trigger if we hit a land
        trigs += trig

        # If we hit a shuffler and the library has fewer than 7 cards left, shuffle up. The odds for loaming are not good.
        if 'shuffler' in found:
            library = createLib(landsInLib, librarySize)
            shuffle(library)
            continue

        # dakmor and shuffler are in last 4 cards
        if len(library) < 5:
            if trigs == 0:
                return (0, 0)

            library = createLib(landsInLib, librarySize)
            shuffle(library)
            continue

    return (0, 0)  # failed


def handle_dredge_6(library, trigs, landsInLib, librarySize):
    # Used as a tally to add back lands when a starting trigger is used
    starting_trigs = trigs

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

        # add a trigger if we hit a land
        trigs += trig

        # If we hit a shuffler and the library has fewer than 7 cards left, shuffle up. The odds for loaming are not good.
        if 'shuffler' in found and len(library) <= 7:
            library = createLib(landsInLib, librarySize)
            shuffle(library)
            continue

        # If there are 7 or fewer cards left in library, we want to shuffle up (dredging here would result in an opponent being able to force us to draw)
        if len(library) < 6:

            # If we hit a land off the last mill, we have to consume that draw trigger before shuffling
            if trig > 0:
                # We must draw one
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

            if trigs == 0:
                return (0, 1)

            library = createLib(landsInLib, librarySize)
            shuffle(library)
            continue

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
              f'Percent occurrence: {round((stat_dict[key][0] + stat_dict[key][1]) * 100 / total_sim_count, 2)},\n\t' +
              f'Success count: {stat_dict[key][1]:,}\n\t' +
              f'Failure count: {stat_dict[key][0]:,}\n\t' +
              f'Success rate: {round(stat_dict[key][1]/(stat_dict[key][0] + stat_dict[key][1]), 2)}')


# Used to run a range of library sizes
def sim_multiple_deck_sizes(landRatioList, minLibrary, maxLibrary, minTriggers=1, maxTriggers=4):
    inputs = []
    for librarySize in range(minLibrary, maxLibrary + 1, 1):
        inputs.append((landRatioList, minTriggers, maxTriggers, librarySize))

    # Multiprocessing
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

    # generate the land ratios by using land counts in an 85 card deck
    for librarySize in range(22, 29):
        landRatioList.append(librarySize / 85)

    startTime = time()
    results, stats, total_sim_count = sim_multiple_deck_sizes(
        landRatioList, 65, 85)

    print(
        f'This is an average from a library size of 65 to 85.\nTotal number of sims: {total_sim_count:,}. Total time: {round(time() - startTime, 2)} secs.\n')
    display_results(results, stats, total_sim_count, landRatioList)
