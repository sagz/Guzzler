import urllib.request
import sys
import time
import multiprocessing
from multiprocessing import Pool
import queue
import guzzler
import functools
import signal

URLS_FILE = 'urls.txt'
FREQUENCY_OF_CONSOLE_UPDATE_SECONDS = 0.01  # Update every 10 milliseconds


def main():
    '''
    Starts Guzzling processes based on optional user commandline arguments and exits
    '''
    urls = guzzler.read_urls(URLS_FILE)

    bound_type, limit = guzzler.set_args()
    start_time = time.time()
    
    manager = multiprocessing.Manager()
    q = manager.Queue()
    stop_event = manager.Event()
    
    p = Pool()

    workers = p.map_async(
        functools.partial(guzzler.guzzle, bound_type, limit, start_time, q, stop_event), urls)

    p.close()

    local_total_downloaded_bytes = 0

    print('Guzzling started.')

    while not workers.ready():
        time.sleep(FREQUENCY_OF_CONSOLE_UPDATE_SECONDS)
        
        while True:
            try:
                chunk = q.get_nowait()
                local_total_downloaded_bytes += chunk
            except queue.Empty:
                break
                
        if bound_type == 'data' and local_total_downloaded_bytes >= limit:
            stop_event.set()
            print(guzzler.guzzle_status(start_time, local_total_downloaded_bytes), end="")
            break

        print(guzzler.guzzle_status(start_time, local_total_downloaded_bytes), end="")

    # Final drain to ensure we don't drop any final updates
    while True:
        try:
            chunk = q.get_nowait()
            local_total_downloaded_bytes += chunk
        except queue.Empty:
            break

    # Print final status once
    print(guzzler.guzzle_status(start_time, local_total_downloaded_bytes), end="")

    p.join()
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
