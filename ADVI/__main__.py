import argparse
import sys

from .build import convert


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=str)
    parser.add_argument("-o", "--output", type=str)
    parser.add_argument("--nperseg", type=int, default=1023)
    parser.add_argument("--fps", type=int, default=18)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height_pad", type=int, default=130)
    parser.add_argument("--width_pad", type=int, default=70)
    parser.add_argument("--margin", type=int, default=1)
    parser.add_argument("--minimum_width", type=int, default=1)
    parser.add_argument("--color", nargs="+", default=[220, 220, 220])
    parser.add_argument("--quite", action="store_true", default=[220, 220, 220])
    args = parser.parse_args(argv)
    return args


if __name__ == "__main__":
    convert(main())
