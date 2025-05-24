import sys

if __name__ == "__main__":
    # test
    if len(sys.argv) >= 2:
        command = sys.argv[1]
        print(command)
        sys.exit(1)
    else:
        print("Please input a command.")
        sys.exit(1)