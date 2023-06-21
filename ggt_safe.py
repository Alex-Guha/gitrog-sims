# some parts co-opted from Spleenface

import random
import tqdm

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
            return 1

        elif 'loam' in found:
            found_loam = True

        trigs += trig  # add a trigger if we hit a land

        if 'shuffler' in found and not first_shuffler_found:
            first_shuffler_found = True

        # TODO If there are > 40 cards in library, we can continue dredging after hitting the second shuffler. This consumes a draw trigger, and if we get down to libsize < 5, we draw instead of dredging
        if 'shuffler' in found and first_shuffler_found:
            found_loam = False
            first_shuffler_found = False
            lib = createLib(landsInLib, libSize)
            random.shuffle(lib)
            continue

        # got through whole library
        if len(lib) < 6:
            print('got through lib')

            # This is the only case where you would dredge loam
            if trigs > 0 and len(lib) == 5 and found_loam:
                trigs -= 1
                lib, trig, found = dredge(3, lib)  # Dredge Loam

                instances_of_shuffler = 0
                for item in found:
                    if item == 'shuffler':
                        instances_of_shuffler += 1

                # There is a shuffler in the next 2 cards
                if found[0] == 'dakmor' and instances_of_shuffler != 2 and not first_shuffler_found:
                    return 1

                # TODO count lands to determine if we should shuffle or take dakmor.
                # If there is a land in the last 2, we cannot take dakmor or we mill ourselves
                elif found[0] == 'dakmor' and instances_of_shuffler == 2:
                    return 1

                # Dakmor is in the last two, risk it for the draw
                elif instances_of_shuffler > 0 and trig == 1:
                    if trigs > 0:
                        return 1
                    trig -= 1
                    card = lib.pop(0)
                    if card == 'dakmor':  # GGEZ wasn't even close btw #calculated
                        return 1
                    elif card == 'land':  # Found new fodder to discard
                        return 1
                    print('failstate')
                    return 0  # Out of draws

                # Dakmor is in the last two but we must shuffle
                elif instances_of_shuffler > 0 and trig == 0:
                    if trigs > 0:
                        trigs -= 1
                        card = lib.pop(0)
                        if card == 'dakmor':  # GGEZ wasn't even close btw #calculated
                            return 1
                        elif card == 'land':  # Found new fodder to discard
                            return 1
                        if trigs > 0:
                            return 1
                    print('failstate')
                    return 0  # Out of draws

                # The last shuffler and dakmor are the last 2 cards, risk it for the draw
                elif instances_of_shuffler == 0 and trig == 1:
                    if trigs > 0:
                        return 1
                    trig -= 1
                    card = lib.pop(0)
                    if card == 'dakmor':  # GGEZ wasn't even close btw #calculated
                        return 1
                    print('failstate')
                    return 0  # Out of draws

                # The last shuffler and dakmor are the last 2 cards, but there's nothing we can do
                elif instances_of_shuffler == 0 and trig == 0:
                    if trigs > 0:
                        trigs -= 1
                        card = lib.pop(0)
                        if card == 'dakmor':  # GGEZ wasn't even close btw #calculated
                            return 1
                        elif card == 'land':  # Found new fodder to discard
                            return 1
                        if trigs > 0:
                            return 1
                    print('failstate')
                    return 0  # Out of draws

            elif trigs > 0:  # If we do not have loam, draw one
                while trigs > 0:
                    trigs -= 1

                    card = lib.pop(0)
                    if card == 'dakmor':  # GGEZ wasn't even close btw #calculated
                        return 1
                    elif card == 'land':  # Found new fodder to discard
                        trigs += 1
                    # If hit shuffler or nonland, do nothing
                print('failstate')
                return 0  # Out of draws

    return 0  # failed


# Accepts a number of lands in the library, size of the library, and number of triggers we can generate
def sim(trigs):
    succ = 0

    # Creates the library as a shuffled array containing 'l' for land, 'd' for dakmor, and 'n' for nonland
    lib = createLib(landsInLib, libSize)

    # Run the simulation 1000 times
    for _ in range(1000):

        random.shuffle(lib)

        # Sum the number of times the sim hit dakmor
        succ += handle_dredge(lib.copy(), trigs)

    # Return the success rate as a percentage
    return round(succ / 10, 1)


# Accepts a range of lands remaining in the deck, number of draw triggers we can generate separately, and library size
def ggt(minLands, maxLands, minTriggers, maxTriggers, librarySize):
    global landsInLib
    global libSize
    result = []
    libSize = librarySize

    for numLands in tqdm.tqdm(range(minLands, maxLands)):
        landsInLib = numLands
        # Used to display the "numLands: "
        result.append([str(numLands) + ":  "])

        # We can restart the dredging with draw triggers we generate, if we hit no lands on a mill.
        # The number of such triggers we can generate is this range.
        for triggers in range(minTriggers, maxTriggers):
            result[numLands - minLands].append(sim(triggers))

    # Display the results
    titleString = "Trigs:  "
    for triggers in range(minTriggers, maxTriggers):  # Create title string
        titleString = titleString + str(triggers) + "     "
    print(titleString)
    print('\n'.join(
        [' '.join([str('{:5}').format(item) for item in row])for row in result]))

    return result


if __name__ == "__main__":
    # PARAMETERS - Change these to simulate whatever scenario you like
    ggt(15, 31, 1, 5, 80)
    ggt(15, 31, 1, 5, 80)
    ggt(15, 31, 1, 5, 80)
