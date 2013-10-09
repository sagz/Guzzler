import urllib.request
import sys
import time
import multiprocessing
from multiprocessing import Pool, Value
from ctypes import c_ulong
#import guzzler
import argparse


def main():
    #urls = read_urls('urls.txt')

    parser = argparse.ArgumentParser(description="""Guzzle Away!
        Guzzler is a tool that will guzzle your internet bandwidth. It does this by downloading 
        packages from many high-speed servers and discarding them instantly.
        This is helpful if you want to know the true sustainable bancwidth of your internet.
        """)

    bound = parser.add_mutually_exclusive_group()

    bound.add_argument("-s", "--seconds", type=int,
                       help="Number of seconds to guzzle away.\nDefault is forever.")
    bound.add_argument("-m", "--minutes", type=int,
                       help="Number of minutes to guzzle away.\nDefault is forever.")
    bound.add_argument("-hr", "--hours", type=int,
                       help="Number of hours to guzzle away.\nDefault is forever.")
    bound.add_argument("-d", "--days", type=int,
                       help="Number of days to guzzle away.\nDefault is forever.")
    bound.add_argument("-mb", "--megabytes", type=int,
                       help="Number of megabytes to download.\nDefault is time-bound to run forever.")
    bound.add_argument("-gb", "--gigabytes", type=int,
                       help="Number of gigabytes to download.\nDefault is time-bound to run forever.")
    bound.add_argument("-tb", "--terabytes", type=int,
                       help="Number of terabytes to download.\nDefault is time-bound to run forever.")
    bound.add_argument("-r", "--rounds", type=int,
                       help="Number of rounds of downloads.\nDefault is 1000")

    parser.add_argument("-p", "--processes", type=int,
                        help="Number of guzzling processes to run simultaneously.\nDefault is 4")

    args = parser.parse_args()

    if args.seconds:
        print(args.seconds)


if __name__ == '__main__':
    main()
