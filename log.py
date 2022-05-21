import sys


def log(m):
    print(m, file=sys.stderr)


class ProgressPrinter:
    def __init__(self, n):
        self.n = n

    def update(self, i):
        s = f"{i / self.n * 100:.1f}% ({i} of {self.n})"
        print("\r" + s + "\033[K", end="", file=sys.stderr)

    def print(self, s):
        print("\n" + s, file=sys.stderr)

    def __enter__(self):
        return self

    def __exit__(self, _1, _2, _3):
        print("", end="\n", file=sys.stderr)
