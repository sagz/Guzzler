import urllib.request
import sys
import time
import multiprocessing
from multiprocessing import Pool, Value
from ctypes import c_ulong


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

time_bound = False
time_limit = 0

data_bound = False
data_limit = 0

not_enough = True
rounds = 1000


if len(sys.argv) > 1:
    if sys.argv[1][-1] == 's' or sys.argv[1][-1] == 'S':
        try:
            time_bound = True
            time_limit = int(sys.argv[1][0:-1])
            print('Guzzler started for %d seconds' % int(sys.argv[1][0:-1]))
        except ValueError:
            pass
    elif sys.argv[1][-1] == 'm' or sys.argv[1][-1] == 'M':
        try:
            time_bound = True
            time_limit = int(sys.argv[1][0:-1]) * 60
            print('Guzzler started for %d minutes' % int(sys.argv[1][0:-1]))
        except ValueError:
            pass
    elif sys.argv[1][-1] == 'h' or sys.argv[1][-1] == 'H':
        try:
            time_bound = True
            time_limit = int(sys.argv[1][0:-1]) * 60 * 60
            print('Guzzler started for %d hours' % int(sys.argv[1][0:-1]))
        except ValueError:
            pass
    elif sys.argv[1][-1] == 'd' or sys.argv[1][-1] == 'D':
        try:
            time_bound = True
            time_limit = int(sys.argv[1][0:-1]) * 60 * 60 * 24
            print('Guzzler started for %d days' % int(sys.argv[1][0:-1]))
        except ValueError:
            pass
    elif sys.argv[1][-1] == 'b' or sys.argv[1][-1] == 'B':
        if sys.argv[1][-2] == 'm' or sys.argv[1][-2] == 'M':
            try:
                data_bound = True
                data_limit = int(sys.argv[1][0:-2])
                print('Guzzler started for %d megabytes' % int(sys.argv[1][0:-2]))
            except ValueError:
                pass
        elif sys.argv[1][-2] == 'G' or sys.argv[1][-2] == 'G':
            try:
                data_bound = True
                data_limit = int(sys.argv[1][0:-2]) * 1024
                print('Guzzler started for %d gigabytes' % int(sys.argv[1][0:-2]))
            except ValueError:
                pass
        elif sys.argv[1][-2] == 't' or sys.argv[1][-2] == 'T':
            try:
                data_bound = True
                data_limit = int(sys.argv[1][0:-2]) * 1024 * 1024
                print('Guzzler started for %d terabytes' % int(sys.argv[1][0:-2]))
            except ValueError:
                pass
    else:
        try:
            if int(sys.argv[1]) > 0:
                rounds = int(sys.argv[1])
                print('Guzzler started for %d rounds' % int(sys.argv[1]))
        except ValueError:
            pass

start_time = time.time()

each_data = []
total_data = Value(c_ulong, 0)

BLOCK_SIZE = 1024 * 1024


def guzzle(fileurl, bound_type, limit, start_time):
    """
    Downloads package at url and updates the multi-processing synchronized value 



    """
    round_number = 0
    global not_enough, data_limit, data_bound, time_bound, time_limit, rounds, start_time, total_data, BLOCK_SIZE

    #each_data[multiprocessing.current_process().name] = 0
    while not_enough:
        try:
            u = urllib.request.urlopen(fileurl)
        except urllib.error.URLError:
            print('\rInternet problems, bro')
            continue

        file_size = int(u.getheader("Content-Length"))

        file_size_dl = 0

        while True:
            temp_buffer = u.read(block_sz)
            if not temp_buffer:
                break

            file_size_dl += len(temp_buffer)

            current_guzzled = (round_number * (float(file_size) / (1024 * 1024))) + (
                file_size_dl / (1024 * 1024))

            #each_data[multiprocessing.current_process().name] += (file_size_dl/(1024*1024))
            total_data.value += int(len(buffer) / 1024 / 1024)  # file_size_dl/1024/1024

            if bound_type == 'data':
                if current_guzzled > limit:
                    not_enough = False
                    break  # sys.exit(0)

            elif bound_type == 'time':
                if time.time() - start_time > limit:
                    not_enough = False
                    break  # sys.exit(0)

        round_number += 1

        if not time_bound:
            if round_number >= rounds:
                not_enough = False  # that is, enough is enough.

p = Pool(3)
workers = p.map_async(guzzle, urls)

p.close()

while not workers.ready():
    megabytes_guzzled = total_data.value
    minutes_elapsed = ((time.time() - start_time) / 60)
    average_speed = megabytes_guzzled / minutes_elapsed / 60

    guzzle_status = "\r%d mb guzzled in %.2f minutes with an average speed of %.2fMB/s." % (
        megabytes_guzzled, minutes_elapsed, average_speed)
    print(guzzle_status, end="")

p.join()
