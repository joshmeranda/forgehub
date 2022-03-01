#!/usr/bin/env python3
import render


def main():
    m = render.render("BOOCHIE")

    m = render.render("HIRE ME PLS :)")

    for offset in range(7):
        for i in range(0, len(m), 7):
            if m[i + offset] == 4:
                print('#', end='')
            else:
                print(' ', end='')
        print()


if __name__ == "__main__":
    main()
