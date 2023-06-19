import numpy as np
import matplotlib.pyplot as plt


def draw_7(cards_in_lib, lands_in_lib):
    total_lands_drawn = 0
    for _ in range(7):
        # One is drawn, tabulate odds it's a land. If it is, reduce number of lands in deck. Then, reduce cards in library.
        card_drawn = np.random.choice(
            ['land', 'non-land'], p=[lands_in_lib / cards_in_lib, (cards_in_lib - lands_in_lib) / cards_in_lib])

        if card_drawn == 'land':
            lands_in_lib -= 1
            total_lands_drawn += 1

        cards_in_lib -= 1
    return total_lands_drawn


def main():
    # Start with X lands in library
    lands_in_lib = 34
    data = {}
    total_trials = 100000

    for _ in range(total_trials):
        # Start with 99 cards in lib
        cards_in_lib = 99

        total_lands_drawn = draw_7(cards_in_lib, lands_in_lib)

        if total_lands_drawn > 4 or total_lands_drawn < 2:
            total_lands_drawn = draw_7(cards_in_lib, lands_in_lib)

        if total_lands_drawn not in data:
            data[total_lands_drawn] = 0
        data[total_lands_drawn] += 1

    cont = plt.bar(list(data.keys()), [x / total_trials for x in list(data.values())],
                   color='green', ec='black', width=0.4)
    plt.bar_label(cont)

    plt.xlabel("Number of lands drawn in a 7 card hand")
    plt.ylabel("Percentage")
    plt.title(
        f"100,000 trials, 99 cards in library, mull if lands < 2 or > 4, {lands_in_lib} lands in deck")
    # plt.title(
    #    f"100,000 trials, 99 cards in library, mulligan not considered, {lands_in_lib} lands in deck")
    plt.show()


if __name__ == "__main__":
    main()
