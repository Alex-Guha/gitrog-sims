import random


def dredge(amt, lib):
    trig = 0
    for i in range(amt):  # take the first X out of the library
        c = lib.pop(0)
        if c == "d":  # found dakmor
            return [0, 0, True]
        elif c == "l":  # found a land
            trig = 1
    return [lib, trig, False]


def createLib(lands, size):
    lib = []  # empty library
    for i in range(lands):  # add the requisite number of lands
        lib.append("l")
    lib.append("d")  # add dakmor
    for j in range(size - lands - 1):  # fill with nonlands
        lib.append("n")
    random.shuffle(lib)  # shuffle
    return lib


def DT(lib, trigs):
    while trigs > 0:  # while you still have a draw trigger
        res = dredge(6, lib)
        if res[2]:  # found dakmor
            return 1
        elif len(lib) < 6:  # got through whole library
            return 1
        lib = res[0]
        trigs += res[1]  # add the trigger from dredging back
        trigs -= 1  # remove a trigger
    return 0  # failed


def sim(lands, size, trigs):
    lib = createLib(lands, size)  # create the library
    return DT(lib, trigs)  # dredge tutor using the created library


def maff(lands, size, trigs):  # run the sim 1000 times and return the success rate
    succ = 0
    for i in range(1000):
        succ += sim(lands, size, trigs)
    return succ / 10


def main():
    res = []
    # PARAMETERS - Change these to simulate whatever scenario you like
    minLands = 15  # inclusive
    maxLands = 31  # exclusive
    minTriggers = 1  # inclusive
    maxTriggers = 4  # exclusive
    libSize = 90

    for i in range(minLands, maxLands):  # iterate through land range
        res.append([str(i) + ":  "])
        for j in range(minTriggers, maxTriggers):  # Iterate through trigger range
            res[i - minLands].append(maff(i, libSize, j))
    titleString = "Trigs:  "
    for i in range(minTriggers, maxTriggers):  # Create title string
        titleString = titleString + str(i) + "     "
    print(titleString)
    print('\n'.join(
        [' '.join([str('{:5}').format(item) for item in row])for row in res]))
    return res


if __name__ == "__main__":
    main()
