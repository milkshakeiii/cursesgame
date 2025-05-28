import sys
from enum import Enum


if __name__ == "__main__":
    # test
    if len(sys.argv) != 2:
        print("Usage: python builder.py <number>")
        sys.exit(1)
    try:
        number = int(sys.argv[1])
    except ValueError:
        print("Please provide a valid integer.")
        sys.exit(1)
    print(number * 2)

class Battle:
    def __init__(self):
        self.tick = 0