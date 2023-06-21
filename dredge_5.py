# some parts co-opted from Spleenface

import random
import tqdm
from collections import Counter

landsInLib = 0
libSize = 0


def dredge(amt, lib):
    trig = 0
    found = []
    for i in range(amt):  # take the first X out of the library
        card = lib.pop(0)
        if card == "dakmor":  # found dakmor
            # Only dakmor is relevant as the loop ends
            return (0, 0, ['dakmor'])

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

    while trigs > 0:  # while you still have a draw trigger
        trigs -= 1  # remove a trigger for dredging

        if trigs < starting_trigs:
            starting_trigs -= 1
            landsInLib += 1
            libSize += 1

        lib, trig, found = dredge(6, lib)

        if len(found) > 0 and found[0] == 'dakmor':
            return 0

        elif 'loam' in found:
            found_loam = True

        trigs += trig  # add a trigger if we hit a land

        if 'shuffler' in found and not first_shuffler_found:
            first_shuffler_found = True

        if len(lib) == 6 or len(lib) == 7:
            print('draw case')
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

            # This is the only case where you would dredge loam
            if trigs > 0 and len(lib) == 5 and found_loam:
                trigs -= 1
                lib, trig, found = dredge(3, lib)  # Dredge Loam

                instances_of_shuffler = 0
                for item in found:
                    if item == 'shuffler':
                        instances_of_shuffler += 1

                # There is a shuffler in the next 2 cards
                if len(found) > 0 and found[0] == 'dakmor' and instances_of_shuffler != 2 and not first_shuffler_found:
                    return 0

                # If there is a land in the last 2, we cannot take dakmor or we mill ourselves
                elif len(found) > 0 and found[0] == 'dakmor' and instances_of_shuffler == 2:
                    if 'land' in lib:
                        return 1
                    else:
                        return 0

                # Dakmor is in the last two, risk it for the draw
                elif instances_of_shuffler > 0 and trig == 1:
                    if trigs > 0:
                        return 0
                    trig -= 1
                    card = lib.pop(0)
                    if card == 'dakmor':  # GGEZ wasn't even close btw #calculated
                        return 0
                    elif card == 'land':  # Found new fodder to discard
                        return 0
                    return 2  # Out of draws

                # Dakmor is in the last two but we must shuffle
                elif instances_of_shuffler > 0 and trig == 0:
                    if trigs > 0:
                        trigs -= 1
                        card = lib.pop(0)
                        if card == 'dakmor':  # GGEZ wasn't even close btw #calculated
                            return 0
                        elif card == 'land':  # Found new fodder to discard
                            return 0
                        if trigs > 0:
                            return 0
                    return 3  # Out of draws

                # The last shuffler and dakmor are the last 2 cards, risk it for the draw
                elif instances_of_shuffler == 0 and trig == 1:
                    if trigs > 0:
                        return 0
                    trig -= 1
                    card = lib.pop(0)
                    if card == 'dakmor':  # GGEZ wasn't even close btw #calculated
                        return 0
                    return 4  # Out of draws

                # The last shuffler and dakmor are the last 2 cards, but there's nothing we can do
                elif instances_of_shuffler == 0 and trig == 0:
                    if trigs > 0:
                        trigs -= 1
                        card = lib.pop(0)
                        if card == 'dakmor':  # GGEZ wasn't even close btw #calculated
                            return 0
                        elif card == 'land':  # Found new fodder to discard
                            return 0
                        if trigs > 0:
                            return 0
                    return 5  # Out of draws

            elif first_shuffler_found:
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

            elif trigs > 0:  # If we do not have loam, draw one
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

    # Run the simulation 1000 times
    for i in range(1000000):
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
    return round(succ / 10000, 1), fails


# Accepts a range of lands remaining in the deck, number of draw triggers we can generate separately, and library size
def ggt(minLands, maxLands, minTriggers, maxTriggers, librarySize):
    global landsInLib
    global libSize
    result = []
    fails = []
    libSize = librarySize

    for numLands in tqdm.tqdm(range(minLands, maxLands)):

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

    # Display the results
    titleString = "Trigs:  "
    for triggers in range(minTriggers, maxTriggers):  # Create title string
        titleString = titleString + str(triggers) + "     "
    print(titleString)
    print('\n'.join(
        [' '.join([str('{:5}').format(item) for item in row])for row in result]))

    # Print failure cases
    type_counts = Counter(fails)
    labels = list(type_counts.keys())
    values = list(type_counts.values())
    labels.reverse()
    values.reverse()

    for i, label in enumerate(labels):
        print(f'Failure type: {label}, Occurrances: {values[i]}')

    return result


if __name__ == "__main__":
    # PARAMETERS - Change these to simulate whatever scenario you like
    ggt(15, 31, 1, 4, 80)
