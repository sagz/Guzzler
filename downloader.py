import urllib.request
import sys
import time
import multiprocessing
from multiprocessing import Pool, Manager
import guzzler
import functools
import signal
import threading

URLS_FILE = 'urls.txt'
FREQUENCY_OF_CONSOLE_UPDATE_SECONDS = 0.01  # Update every 10 milliseconds

total_downloaded_bytes_local = 0

def aggregator(queue, stop_event, bound_type, limit):
    global total_downloaded_bytes_local
    while True:
        item = queue.get()
        if item is None:
            break
        total_downloaded_bytes_local += item
        if bound_type == 'data' and total_downloaded_bytes_local >= limit:
            stop_event.set()

def main():
    '''
    Starts Guzzling processes based on optional user commandline arguments and exits
    '''
    urls = guzzler.read_urls(URLS_FILE)

    bound_type, limit = guzzler.set_args()
    start_time = time.time()
    
    manager = Manager()
    queue = manager.Queue()
    stop_event = manager.Event()

    aggr_thread = threading.Thread(target=aggregator, args=(queue, stop_event, bound_type, limit))
    aggr_thread.start()

    p = Pool()

    workers = p.map_async(
        functools.partial(guzzler.guzzle, bound_type, limit, start_time, queue, stop_event), urls)

    p.close()

    print('Guzzling started.')

    while not workers.ready():
        time.sleep(FREQUENCY_OF_CONSOLE_UPDATE_SECONDS)
        print(guzzler.guzzle_status(start_time, total_downloaded_bytes_local), end="")

    p.join()
    
    # Gracefully shut down the aggregator
    queue.put(None)
    aggr_thread.join()
    
    # Print the final status
    print(guzzler.guzzle_status(start_time, total_downloaded_bytes_local), end="")
    print()


def SIGINT_handler(signal, frame):
    '''
    Gracefully exits on KeyboardInterrupt
    signal and frame are parameters with traceback information.
    '''
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, SIGINT_handler)
    main()
