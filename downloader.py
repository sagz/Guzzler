import urllib.request
import sys
import time
import multiprocessing
from multiprocessing import Pool, Value
from ctypes import c_ulong
import guzzler
import functools
import signal

URLS_FILE = 'urls.txt'


def main():
    urls = guzzler.read_urls(URLS_FILE)

    bound_type, limit = guzzler.set_args()
    start_time = time.time()

    p = Pool()
    workers = p.map_async(
        functools.partial(guzzler.guzzle, bound_type, limit, start_time), urls)

    p.close()

    while not workers.ready():
        print(guzzler.guzzle_status(start_time), end="")

    graceful_exit(p)


def SIGINT_handler(signal, frame):
    graceful_exit()


def graceful_exit(p):
    p.join()
    print()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, graceful_exit)
    main()
