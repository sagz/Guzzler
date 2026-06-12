import urllib.request
import urllib.parse
import sys
import time
import socket
import ssl
import struct
from multiprocessing import Value
from ctypes import c_ulonglong
import argparse

total_downloaded_bytes = Value(c_ulonglong, 0)
shared_retrans = Value(c_ulonglong, 0)
shared_lost = Value(c_ulonglong, 0)
shared_rtt = Value(c_ulonglong, 0)
shared_cwnd = Value(c_ulonglong, 0)

BLOCK_SIZE = 1024 * 1024

SECONDS_PER_MINUTE = 60
MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24

BYTES_PER_MEGABYTE = 1024 * 1024
MEGABYTES_PER_GIGABYTE = 1024
GIGABYTES_PER_TERABYTE = 1024

# 1000 years.
DEFAULT_MAXIMUM_TIME = 1000 * 365 * HOURS_PER_DAY * MINUTES_PER_HOUR * SECONDS_PER_MINUTE

DOWNLOADED_DATA_COLOUR = '38;05;42'
TIME_ELAPSED_COLOUR = '38;05;217'
AVERAGE_SPEED_COLOUR = '38;05;110'


def set_args():
    '''
    Collects and parses the command line arguments. All arguments are optional.
    Returns bound_type and limit.
    bound_type : string with either of two values
                'data' means guzzling is limited by data
                'time' mean guzzling is limited by time
    limit : raw value of limit
            if bound_type is 'data', limit is the number of bytes
            if bound_type is 'time', limit is the number of seconds
    '''

    parser = argparse.ArgumentParser(description='''Guzzle Away!
        Guzzler is a tool that will guzzle your internet bandwidth. It does this by downloading 
        packages from many high-speed servers and discarding them instantly.
        This is helpful if you want to know the true sustainable bandwidth of your internet.
        ''')

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


def colour(this_color, string):
    '''
    Returns pretty string output in colour. ANSI 256 colour mode.
    
    Print all 256 colours with code snippet-
    --------------------------------------------------------------
        def color(this_color, string):
            return "\033[" + this_color + "m" + string + "\033[0m"
        for i in range(256):
            c = '38;05;%d' % i
            print( color(c, 'color ' + c) )
    --------------------------------------------------------------

    this_color : ANSI Escape sequence corresponding to a colour
    string : string that is needed in the colour
    '''
    return "\033[" + this_color + "m" + string + "\033[0m"


last_check_time = 0
last_check_bytes = 0

def guzzle_status(start_time):
    '''
    Makes a string of the current guzzling status.

    start_time: timestamp in seconds of when guzzling process started

    returns string with megabytes guzzled and average speed
    '''
    global last_check_time, last_check_bytes
    current_time = time.time()
    current_bytes = total_downloaded_bytes.value

    megabytes_guzzled = current_bytes / BYTES_PER_MEGABYTE
    minutes_elapsed = ((current_time - start_time) / SECONDS_PER_MINUTE)
    
    interval_time = current_time - last_check_time
    if last_check_time > 0 and interval_time > 0:
        interval_speed = ((current_bytes - last_check_bytes) / BYTES_PER_MEGABYTE) / interval_time
    else:
        interval_speed = 0.0
        
    last_check_time = current_time
    last_check_bytes = current_bytes

    megabytes_guzzled_str = colour(DOWNLOADED_DATA_COLOUR, '%.2f mb' % megabytes_guzzled)
    minutes_elapsed_str = colour(TIME_ELAPSED_COLOUR, '%.2f minutes' % minutes_elapsed)
    average_speed_str = colour(AVERAGE_SPEED_COLOUR, '%.2fMB/s' % interval_speed)
    
    retrans_str = colour('38;05;196', 'Retrans: %d' % shared_retrans.value)
    lost_str = colour('38;05;208', 'Loss: %d' % shared_lost.value)
    rtt_str = colour('38;05;220', 'RTT: %.2fms' % (shared_rtt.value / 1000.0))
    cwnd_str = colour('38;05;46', 'CWND: %d' % shared_cwnd.value)

    guzzle_status = "\r%s guzzled in %s | Speed: %s | %s | %s | %s | %s          " % (
        megabytes_guzzled_str, minutes_elapsed_str, average_speed_str, retrans_str, lost_str, rtt_str, cwnd_str)

    return guzzle_status


def guzzle(bound_type, limit, start_time, url):
    '''
    Downloads package at url and updates the multiprocessing-synchronized value "total_downloaded_bytes"

    url : the file url being fetched
    bound_type : string with either of two values
                'data' means guzzling is limited by data
                'time' mean guzzling is limited by time
    limit : raw value of limit
            if bound_type is 'data', limit is the number of bytes
            if bound_type is 'time', limit is the number of seconds
    start_time : time when guzzling started
    '''
    global total_downloaded_bytes
    global shared_retrans, shared_lost, shared_rtt, shared_cwnd

    while (bound_type == 'data' and total_downloaded_bytes.value < limit) or (bound_type == 'time' and time.time() - start_time < limit):
        try:
            parsed = urllib.parse.urlparse(url)
            host = parsed.hostname
            port = parsed.port or (443 if parsed.scheme == 'https' else 80)
            
            sock = socket.create_connection((host, port), timeout=5)
            if parsed.scheme == 'https':
                ctx = ssl.create_default_context()
                sock = ctx.wrap_socket(sock, server_hostname=host)
                
            request = f"GET {parsed.path or '/'} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
            sock.sendall(request.encode('utf-8'))
        except Exception:
            print('\rInternet problems, bro')
            continue
            
        last_tcp_bytes = 0
        last_retrans = 0
        last_lost = 0

        while (bound_type == 'data' and total_downloaded_bytes.value < limit) or (bound_type == 'time' and time.time() - start_time < limit):
            try:
                temp_buffer = sock.recv(BLOCK_SIZE)
                if not temp_buffer:
                    break
                    
                # Try to fetch TCP telemetry using standard TCP_INFO
                tcp_info_supported = hasattr(socket, 'TCP_INFO')
                tcp_info_success = False
                
                if tcp_info_supported:
                    try:
                        info = sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_INFO, 248)
                        fmt = '8B 24I 4Q 2I'
                        size = struct.calcsize(fmt)
                        if len(info) >= size:
                            unpacked = struct.unpack(fmt, info[:size])
                            
                            rtt = unpacked[23]
                            cwnd = unpacked[26]
                            total_retrans_val = unpacked[31]
                            lost = unpacked[14]
                            bytes_received = unpacked[35]
                            
                            new_bytes = bytes_received - last_tcp_bytes
                            new_retrans = total_retrans_val - last_retrans
                            new_lost = lost - last_lost
                            
                            last_tcp_bytes = bytes_received
                            last_retrans = total_retrans_val
                            last_lost = lost
                            
                            if new_bytes > 0:
                                total_downloaded_bytes.value += new_bytes
                            if new_retrans > 0:
                                shared_retrans.value += new_retrans
                            if new_lost > 0:
                                shared_lost.value += new_lost
                                
                            shared_rtt.value = rtt
                            shared_cwnd.value = cwnd
                            
                            tcp_info_success = True
                    except Exception:
                        pass
                
                # Fallback to application-layer counting if TCP_INFO is unavailable
                if not tcp_info_success:
                    total_downloaded_bytes.value += len(temp_buffer)
            except Exception:
                break
        
        try:
            sock.close()
        except Exception:
            pass
