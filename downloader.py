import urllib.request
import sys
import time
import multiprocessing
from multiprocessing import Pool, Value
from ctypes import c_ulong
import guzzler
import functools

PROCESSES = 3
URLS_FILE = 'urls.txt'


def main():
    urls = guzzler.read_urls(URLS_FILE)

    bound_type, limit = guzzler.set_args()
    start_time = time.time()

    p = Pool(PROCESSES)
    workers = p.map_async(
        functools.partial(guzzler.guzzle, bound_type, limit, start_time), urls)

    p.close()

    while not workers.ready():
        megabytes_guzzled = guzzler.total_downloaded_bytes.value / guzzler.BYTES_PER_MEGABYTE
        minutes_elapsed = ((time.time() - start_time) / guzzler.SECONDS_PER_MINUTE)
        average_speed = megabytes_guzzled / minutes_elapsed / guzzler.SECONDS_PER_MINUTE

        guzzle_status = "\r%d mb guzzled in %.2f minutes with an average speed of %.2fMB/s." % (
            megabytes_guzzled, minutes_elapsed, average_speed)

        print(guzzle_status, end="")

    p.join()

    print()

if __name__ == '__main__':
    main()
