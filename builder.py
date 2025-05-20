import sys

# console application that prints twice whatever number is passed to it as an argument
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python builder.py <number>")
        sys.exit(1)
    
    try:
        number = int(sys.argv[1])
    except ValueError:
        print("Please provide a valid integer.")
        sys.exit(1)
    print(number * 2)