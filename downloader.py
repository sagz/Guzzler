import urllib.request
import sys
import time
import multiprocessing
from multiprocessing import Pool, Value
from ctypes import c_ulong
import guzzler
import functools
import signal
import json

URLS_FILE = 'urls.txt'
FREQUENCY_OF_CONSOLE_UPDATE_SECONDS = 0.01  # Update every 10 milliseconds


def main():
    '''
    Starts Guzzling processes based on optional user commandline arguments and exits
    '''
    urls = guzzler.read_urls(URLS_FILE)

    bound_type, limit = guzzler.set_args()
    start_time = time.time()
    p = Pool()

    workers = p.map_async(
        functools.partial(guzzler.guzzle, bound_type, limit, start_time), urls)

    p.close()

    print('Guzzling started.')
    
    export_data = []
    last_time = time.time()
    last_bytes = 0

    while not workers.ready():
        time.sleep(FREQUENCY_OF_CONSOLE_UPDATE_SECONDS)
        
        current_time = time.time()
        current_bytes = guzzler.total_downloaded_bytes.value
        interval = current_time - last_time
        
        if interval > 0:
            speed = (current_bytes - last_bytes) / interval
        else:
            speed = 0.0
            
        last_time = current_time
        last_bytes = current_bytes
        
        # Collect sample for structured data export
        export_data.append({
            "timestamp": current_time,
            "interval_s": interval,
            "throughput_bps": speed,
            "retransmissions": guzzler.shared_retrans.value,
            "packet_loss": guzzler.shared_lost.value,
            "rtt_us": guzzler.shared_rtt.value,
            "cwnd": guzzler.shared_cwnd.value
        })
        
        print(guzzler.guzzle_status(start_time), end="")

    p.join()
    print()
    
    # Write structured export data
    try:
        with open('ndt_export.json', 'w') as f:
            json.dump(export_data, f, indent=2)
        print("Exported telemetry to ndt_export.json")
    except Exception as e:
        print(f"Failed to export telemetry: {e}")


def SIGINT_handler(signal, frame):
    '''
    Gracefully exits on KeyboardInterrupt
    signal and frame are parameters with traceback information.
    '''
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, SIGINT_handler)
    main()
