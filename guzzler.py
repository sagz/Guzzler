import urllib.request
import sys
import socket
import struct
import time
from multiprocessing import Value
from ctypes import c_ulonglong
import argparse

total_downloaded_bytes = Value(c_ulonglong, 0)
cumulative_retransmissions = Value(c_ulonglong, 0)
current_cwnd = Value(c_ulonglong, 0)
total_successful_payloads = Value(c_ulonglong, 0)
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


    parser.add_argument("--include-overhead", action="store_true",
                       help="Account for estimated protocol overhead in throughput calculations.")

    args = parser.parse_args()
    include_overhead = args.include_overhead

    if args.seconds:
        return 'time', args.seconds, include_overhead
    elif args.minutes:
        return 'time', args.minutes * SECONDS_PER_MINUTE, include_overhead
    elif args.hours:
        return 'time', args.hours * MINUTES_PER_HOUR * SECONDS_PER_MINUTE, include_overhead
    elif args.days:
        return 'time', args.days * HOURS_PER_DAY * MINUTES_PER_HOUR * SECONDS_PER_MINUTE, include_overhead

    elif args.megabytes:
        return 'data', args.megabytes * BYTES_PER_MEGABYTE, include_overhead
    elif args.gigabytes:
        return 'data', args.gigabytes * MEGABYTES_PER_GIGABYTE * BYTES_PER_MEGABYTE, include_overhead
    elif args.terabytes:
        return 'data', args.terabytes * GIGABYTES_PER_TERABYTE * MEGABYTES_PER_GIGABYTE * BYTES_PER_MEGABYTE, include_overhead

    else:
        return 'time', DEFAULT_MAXIMUM_TIME, include_overhead


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


def guzzle_status(start_time, include_overhead):
    '''
    Makes a string of the current guzzling status.

    start_time: timestamp in seconds of when guzzling process started

    returns string with megabytes guzzled and average speed
    '''
    
    total_bytes = total_downloaded_bytes.value
    if include_overhead:
        total_overhead_bytes = (cumulative_retransmissions.value * 1500) + (total_bytes / 1448.0) * 52
        total_bytes += total_overhead_bytes

    megabytes_guzzled = total_bytes / BYTES_PER_MEGABYTE
    minutes_elapsed = ((time.time() - start_time) / SECONDS_PER_MINUTE)
    if minutes_elapsed == 0:
        minutes_elapsed = 0.0001
    average_speed = megabytes_guzzled / minutes_elapsed / SECONDS_PER_MINUTE

    # Network health score calculation
    succ = total_successful_payloads.value
    retrans = cumulative_retransmissions.value
    total_pkts = succ + retrans
    health_score = (succ / total_pkts * 100) if total_pkts > 0 else 100.0
    health_label = "Healthy" if health_score >= 95.0 else "Congested/Throttled"

    megabytes_guzzled_str = colour(DOWNLOADED_DATA_COLOUR, '%d mb' % megabytes_guzzled)
    minutes_elapsed_str = colour(TIME_ELAPSED_COLOUR, '%.2f minutes' % minutes_elapsed)
    average_speed_str = colour(AVERAGE_SPEED_COLOUR, '%.2fMB/s' % average_speed)
    
    health_colour = '38;05;46' if health_label == "Healthy" else '38;05;196'
    health_str = colour(health_colour, f"{health_score:.1f}% ({health_label})")
    cwnd_str = colour('38;05;220', str(current_cwnd.value))
    retrans_str = colour('38;05;196', str(cumulative_retransmissions.value))

    guzzle_status_str = "\r%s guzzled in %s with an average speed of %s | CWND: %s | Retrans: %s | Health: %s" % (
        megabytes_guzzled_str, minutes_elapsed_str, average_speed_str, cwnd_str, retrans_str, health_str)

    return guzzle_status_str


def guzzle(bound_type, limit, start_time, include_overhead, url):
    '''
    Downloads package at url and updates the multiprocessing-synchronized value "total_downloaded_bytes"
    '''
    global total_downloaded_bytes
    global cumulative_retransmissions
    global current_cwnd
    global total_successful_payloads

    # parent loop which downloads the same url package till limit is crossed.
    while (bound_type == 'data' and total_downloaded_bytes.value < limit) or (bound_type == 'time' and time.time() - start_time < limit):

        try:
            u = urllib.request.urlopen(url)
            sock = u.fp.raw._sock
        except Exception:
            print('\rInternet problems, bro')
            continue

        last_retrans = 0
        last_succ = 0

        # child loop which downloads partial blocks of the url package till url
        # package is completely downloaded
        while (bound_type == 'data' and total_downloaded_bytes.value < limit) or (bound_type == 'time' and time.time() - start_time < limit):

            try:
                temp_buffer = u.read(BLOCK_SIZE)
            except Exception:
                break

            if not temp_buffer:
                break

            # Kernel telemetry block
            try:
                TCP_INFO = getattr(socket, 'TCP_INFO', 11)
                info = sock.getsockopt(socket.IPPROTO_TCP, TCP_INFO, 1024)
                fmt = "8B 24I 4Q 2I"
                if len(info) >= struct.calcsize(fmt):
                    unpacked = struct.unpack(fmt, info[:struct.calcsize(fmt)])
                    cwnd = unpacked[8+18]
                    total_retrans = unpacked[8+23]
                    segs_out = unpacked[8+24+4+0]
                    segs_in = unpacked[8+24+4+1]
                    
                    current_cwnd.value = cwnd
                    
                    delta_retrans = total_retrans - last_retrans
                    if delta_retrans > 0:
                        with cumulative_retransmissions.get_lock():
                            cumulative_retransmissions.value += delta_retrans
                        last_retrans = total_retrans
                        
                    delta_succ = segs_out - last_succ
                    if delta_succ > 0:
                        with total_successful_payloads.get_lock():
                            total_successful_payloads.value += delta_succ
                        last_succ = segs_out
                else:
                    # Fallback to shorter struct if extended isn't available
                    fmt_short = "8B 24I"
                    if len(info) >= struct.calcsize(fmt_short):
                        unpacked = struct.unpack(fmt_short, info[:struct.calcsize(fmt_short)])
                        cwnd = unpacked[8+18]
                        total_retrans = unpacked[8+23]
                        
                        current_cwnd.value = cwnd
                        
                        delta_retrans = total_retrans - last_retrans
                        if delta_retrans > 0:
                            with cumulative_retransmissions.get_lock():
                                cumulative_retransmissions.value += delta_retrans
                            last_retrans = total_retrans
                            
                        # Estimate payloads if segs_out isn't available
                        delta_succ = len(temp_buffer) // 1448
                        if delta_succ > 0:
                            with total_successful_payloads.get_lock():
                                total_successful_payloads.value += delta_succ
            except Exception:
                pass # Gracefully fallback without crashing on platforms that lack TCP_INFO

            total_downloaded_bytes.value += len(temp_buffer)
