import urllib.request
import sys
import time
from multiprocessing import Value
from ctypes import c_ulonglong
import argparse

total_downloaded_bytes = Value(c_ulonglong, 0)
BLOCK_SIZE = 1024 * 1024

SECONDS_PER_MINUTE = 60
MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24

BYTES_PER_MEGABYTE = 1024 * 1024
MEGABYTES_PER_GIGABYTE = 1024
GIGABYTES_PER_TERABYTE = 1024

# 1000 years.
DEFAULT_MAXIMUM_TIME = 1000 * 365 * HOURS_PER_DAY * MINUTES_PER_HOUR * SECONDS_PER_MINUTE


def set_args():
    """
    Collects and parses the command line arguments. All arguments are optional.
    Returns bound_type and limit.
    bound_type : string with either of two values
                'data' means guzzling is limited by data
                'time' mean guzzling is limited by time
    limit : raw value of limit
            if bound_type is 'data', limit is the number of bytes
            if bound_type is 'time', limit is the number of seconds
    """

    parser = argparse.ArgumentParser(description="""Guzzle Away!
        Guzzler is a tool that will guzzle your internet bandwidth. It does this by downloading 
        packages from many high-speed servers and discarding them instantly.
        This is helpful if you want to know the true sustainable bancwidth of your internet.
        """)

    bound = parser.add_mutually_exclusive_group()

    bound.add_argument("-s", "--seconds", type=int,
                       help="Number of seconds to guzzle away.\nDefault is 1000 years.")
    bound.add_argument("-m", "--minutes", type=int,
                       help="Number of minutes to guzzle away.\nDefault is 1000 years.")
    bound.add_argument("-hr", "--hours", type=int,
                       help="Number of hours to guzzle away.\nDefault is 1000 years.")
    bound.add_argument("-d", "--days", type=int,
                       help="Number of days to guzzle away.\nDefault is 1000 years.")
    bound.add_argument("-mb", "--megabytes", type=int,
                       help="Number of megabytes to download.\nDefault is time-bound to run 1000 years.")
    bound.add_argument("-gb", "--gigabytes", type=int,
                       help="Number of gigabytes to download.\nDefault is time-bound to run 1000 years.")
    bound.add_argument("-tb", "--terabytes", type=int,
                       help="Number of terabytes to download.\nDefault is time-bound to run 1000 years.")

    # parser.add_argument("-p", "--processes", type=int,
    #                    help="Number of guzzling processes to run simultaneously.\nDefault is 4")

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

    else:
        return 'time', DEFAULT_MAXIMUM_TIME


def read_urls(filename):
    '''
    Reads the list of URLs from a text file in the same folder.
    Loads from file and returns a Python list of urls

    filename : name of file in the same folder with URLs (one per line)
    '''
    urls = []
    for line in open(filename):
        # Check for empty/commented lines
        if line and not line.startswith('#') and len(line.strip()) > 5:
            urls.append(line.strip())
    return urls


def guzzle_status(start_time):
    megabytes_guzzled = total_downloaded_bytes.value / BYTES_PER_MEGABYTE
    minutes_elapsed = ((time.time() - start_time) / SECONDS_PER_MINUTE)
    average_speed = megabytes_guzzled / minutes_elapsed / SECONDS_PER_MINUTE

    guzzle_status = "\r%d mb guzzled in %.2f minutes with an average speed of %.2fMB/s." % (
        megabytes_guzzled, minutes_elapsed, average_speed)

    return guzzle_status


def guzzle(bound_type, limit, start_time, url):
    """
    Downloads package at url and updates the multiprocessing-synchronized value "total_downloaded_bytes"

    url : the file url being fetched
    bound_type : string with either of two values
                'data' means guzzling is limited by data
                'time' mean guzzling is limited by time
    limit : raw value of limit
            if bound_type is 'data', limit is the number of bytes
            if bound_type is 'time', limit is the number of seconds
    start_time : time when guzzling started
    """
    global total_downloaded_bytes

    # parent loop which downloads the same url package till limit is crossed.
    while (bound_type == 'data' and total_downloaded_bytes.value < limit) or (bound_type == 'time' and time.time() - start_time < limit):

        try:
            u = urllib.request.urlopen(url)
        except urllib.error.URLError:
            print('\rInternet problems, bro')
            continue

        # child loop which downloads partial blocks of the url package till url
        # package is completely downloaded
        while (bound_type == 'data' and total_downloaded_bytes.value < limit) or (bound_type == 'time' and time.time() - start_time < limit):

            temp_buffer = u.read(BLOCK_SIZE)

            if not temp_buffer:
                break

            total_downloaded_bytes.value += len(temp_buffer)
