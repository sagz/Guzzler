import urllib.request
import sys
import time
import multiprocessing
from multiprocessing import Pool
import queue as q
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
    progress_queue = manager.Queue()
    stop_event = manager.Event()
    
    p = Pool()

    workers = p.map_async(
        functools.partial(guzzler.guzzle, bound_type, limit, start_time, stop_event, progress_queue), urls)

    print('Guzzling started.')
    
    total_downloaded_bytes = 0

    while not workers.ready():
        time.sleep(FREQUENCY_OF_CONSOLE_UPDATE_SECONDS)
        
        while True:
            try:
                chunk_size = progress_queue.get_nowait()
                total_downloaded_bytes += chunk_size
            except q.Empty:
                break
                
        if bound_type == 'data' and total_downloaded_bytes >= limit:
            stop_event.set()
        elif bound_type == 'time' and time.time() - start_time >= limit:
            stop_event.set()
            
        print(guzzler.guzzle_status(start_time, total_downloaded_bytes), end="")

        if stop_event.is_set():
            break

    # Final drain of the queue to ensure perfect accuracy
    while True:
        try:
            chunk_size = progress_queue.get_nowait()
            total_downloaded_bytes += chunk_size
        except q.Empty:
            break

    print(guzzler.guzzle_status(start_time, total_downloaded_bytes), end="")

    p.terminate()
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
