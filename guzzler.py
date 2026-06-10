import urllib.request
import urllib.error
import time
import os
import math
import multiprocessing

shared_total_bytes = None
shared_active_event = None
shared_error_flag = None

def init_worker(total_bytes, active_event, error_flag):
    global shared_total_bytes
    global shared_active_event
    global shared_error_flag
    shared_total_bytes = total_bytes
    shared_active_event = active_event
    shared_error_flag = error_flag

def download_segment_worker(args):
    url, orig_start_byte, end_byte, dest_path, segment_index = args
    
    if not shared_active_event.is_set() or shared_error_flag.is_set():
        return False
        
    current_start_byte = orig_start_byte
    mode = 'wb'
    max_retries = 3
    
    for attempt in range(max_retries + 1):
        if not shared_active_event.is_set() or shared_error_flag.is_set():
            return False
            
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Guzzler-Robust-Manager/1.0')
        if current_start_byte is not None and end_byte is not None:
            req.add_header('Range', f'bytes={current_start_byte}-{end_byte}')
        elif current_start_byte is not None:
            req.add_header('Range', f'bytes={current_start_byte}-')
            
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                with open(dest_path, mode) as f:
                    while True:
                        if not shared_active_event.is_set() or shared_error_flag.is_set():
                            return False
                        chunk = response.read(1024 * 128) # 128 KB chunks
                        if not chunk:
                            break
                        f.write(chunk)
                        chunk_len = len(chunk)
                        if current_start_byte is not None:
                            current_start_byte += chunk_len
                        with shared_total_bytes.get_lock():
                            shared_total_bytes.value += chunk_len
            return True
        except Exception as e:
            if attempt == max_retries:
                shared_error_flag.set()
                print(f"\nError downloading segment {segment_index} of {url}: {e}")
                return False
            
            # Prepare to resume
            if orig_start_byte is not None:
                mode = 'ab'
            else:
                mode = 'wb'
                
            time.sleep(2)
    return False

class DownloadManager:
    def __init__(self, num_workers=4, segment_size=1024*1024*5):
        self.num_workers = num_workers
        self.segment_size = segment_size
        self.total_bytes = multiprocessing.Value('Q', 0)
        self.active_event = multiprocessing.Event()
        self.error_flag = multiprocessing.Event()
        self.pool = None
        self.start_time = None
        self.result = None
        
    def get_file_info(self, url):
        req = urllib.request.Request(url, method='HEAD')
        req.add_header('User-Agent', 'Guzzler-Robust-Manager/1.0')
        max_retries = 3
        for attempt in range(max_retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    length = response.headers.get('Content-Length')
                    accept_ranges = response.headers.get('Accept-Ranges') == 'bytes'
                    return int(length) if length else None, accept_ranges
            except Exception as e:
                if attempt == max_retries:
                    raise e
                time.sleep(1)
        return None, False

    def start_downloads(self, urls, dest_dir="."):
        self.active_event.set()
        self.error_flag.clear()
        self.total_bytes.value = 0
        self.start_time = time.time()
        
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        tasks = []
        self.file_segments = {}

        for url in urls:
            filename = url.split('/')[-1] or "downloaded_file"
            dest_file = os.path.join(dest_dir, filename)
            
            try:
                length, accept_ranges = self.get_file_info(url)
            except Exception as e:
                self.error_flag.set()
                print(f"\nFailed to get info for {url}: {e}")
                return False
                
            if length and accept_ranges:
                num_segments = math.ceil(length / self.segment_size)
                self.file_segments[dest_file] = []
                for i in range(num_segments):
                    start_byte = i * self.segment_size
                    end_byte = min(start_byte + self.segment_size - 1, length - 1)
                    segment_path = f"{dest_file}.part{i}"
                    self.file_segments[dest_file].append(segment_path)
                    tasks.append((url, start_byte, end_byte, segment_path, i))
            else:
                segment_path = f"{dest_file}.part0"
                self.file_segments[dest_file] = [segment_path]
                tasks.append((url, None, None, segment_path, 0))

        self.pool = multiprocessing.Pool(
            processes=self.num_workers,
            initializer=init_worker,
            initargs=(self.total_bytes, self.active_event, self.error_flag)
        )
        self.result = self.pool.map_async(download_segment_worker, tasks)
        return True

    def wait(self):
        if not self.pool:
            return False
            
        try:
            self.result.get()
        except KeyboardInterrupt:
            self.stop()
            return False
            
        self.pool.close()
        self.pool.join()
        
        if not self.active_event.is_set():
            self._cleanup_segments(self.file_segments)
            return False
            
        if self.error_flag.is_set():
            self._cleanup_segments(self.file_segments)
            return False
            
        for dest_file, segments in self.file_segments.items():
            with open(dest_file, 'wb') as outfile:
                for seg in segments:
                    with open(seg, 'rb') as infile:
                        outfile.write(infile.read())
                    os.remove(seg)
                    
        return True

    def _cleanup_segments(self, file_segments):
        for dest_file, segments in file_segments.items():
            for seg in segments:
                if os.path.exists(seg):
                    try:
                        os.remove(seg)
                    except:
                        pass

    def stop(self):
        self.active_event.clear()
        if self.pool:
            self.pool.terminate()
            self.pool.join()

    def get_status(self):
        bytes_down = self.total_bytes.value
        elapsed = time.time() - self.start_time if self.start_time else 0
        speed = bytes_down / elapsed if elapsed > 0 else 0
        return {
            'downloaded_bytes': bytes_down,
            'elapsed_seconds': elapsed,
            'speed_bytes_per_sec': speed,
            'is_active': self.active_event.is_set() and not self.error_flag.is_set(),
            'is_finished': self.result.ready() if self.pool else False
        }
