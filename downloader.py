import urllib.request
import sys
import time
import multiprocessing
from multiprocessing import Pool, Value
from ctypes import c_ulong
#import guzzler
import argparse

SECONDS_PER_MINUTE = 60
MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24

BYTES_PER_MEGABYTE = 1024 * 1024
MEGABYTES_PER_GIGABYTE = 1024
GIGABYTES_PER_TERABYTE = 1024


def set_args():
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
        return 'time', args.seconds
    elif args.minutes:
        return 'time', args.minutes * SECONDS_PER_MINUTE
    elif args.hours:
        return 'time', args.hours * MINUTES_PER_HOUR * SECONDS_PER_MINUTE
    elif args.days:
        return 'time', args.days * HOURS_PER_DAY * MINUTES_PER_HOUR * SECONDS_PER_MINUTE

    elif args.megabytes:
        return 'data', args.megabytes * BYTES_PER_MEGABYTE
    elif args.gigabytes:
        return 'data', args.gigabytes * MEGABYTES_PER_GIGABYTE * BYTES_PER_MEGABYTE
    elif args.terabytes:
        return 'data', args.terabytes * GIGABYTES_PER_TERABYTE * MEGABYTES_PER_GIGABYTE * BYTES_PER_MEGABYTE


def main():
    #urls = read_urls('urls.txt')

    bound_type, limit = set_args()

    print(bound_type, limit)

if __name__ == '__main__':
    main()
