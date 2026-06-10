import sys
import time
import signal
from guzzler import DownloadManager
import os

URLS_FILE = 'urls.txt'
FREQUENCY_OF_CONSOLE_UPDATE_SECONDS = 0.1

manager_instance = None

def SIGINT_handler(signum, frame):
    print("\nStopping downloads...")
    if manager_instance:
        manager_instance.stop()
    sys.exit(0)

def read_urls(filename):
    urls = []
    try:
        for line in open(filename):
            if line and not line.startswith('#') and len(line.strip()) > 5:
                urls.append(line.strip())
    except FileNotFoundError:
        pass
    return urls

def format_bytes(b):
    if b < 1024:
        return f"{b:.0f} B"
    elif b < 1024**2:
        return f"{b/1024:.2f} KB"
    elif b < 1024**3:
        return f"{b/1024**2:.2f} MB"
    else:
        return f"{b/1024**3:.2f} GB"

def colour(this_color, string):
    return "\033[" + this_color + "m" + string + "\033[0m"

def main():
    global manager_instance
    urls = read_urls(URLS_FILE)
    if not urls:
        print(f"No URLs found in {URLS_FILE}")
        return

    print("Starting Multi-threaded Download Manager...")
    # Use 4 workers as standard
    manager_instance = DownloadManager(num_workers=4)
    
    success = manager_instance.start_downloads(urls, dest_dir="downloads")
    if not success:
        print("Failed to start downloads.")
        return
        
    print("Downloading...")
    
    while True:
        status = manager_instance.get_status()
        
        down_str = format_bytes(status['downloaded_bytes'])
        speed_str = format_bytes(status['speed_bytes_per_sec']) + "/s"
        elapsed = status['elapsed_seconds']
        
        c_down = colour('38;05;42', down_str)
        c_time = colour('38;05;217', f"{elapsed:.1f}s")
        c_speed = colour('38;05;110', speed_str)
        
        print(f"\rDownloaded: {c_down} | Speed: {c_speed} | Time: {c_time}    ", end="")
        
        if status['is_finished'] or not status['is_active']:
            break
            
        time.sleep(FREQUENCY_OF_CONSOLE_UPDATE_SECONDS)
        
    print() # Newline
    
    result = manager_instance.wait()
    if result:
        print("All downloads completed successfully.")
    else:
        print("Downloads failed or were cancelled.")

if __name__ == '__main__':
    signal.signal(signal.SIGINT, SIGINT_handler)
    main()
