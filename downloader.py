import urllib2
import sys
import time
import multiprocessing
from multiprocessing import Pool, Value
from ctypes import c_ulong


def read_urls(input_file):
    urls = []
    for line in open(input_file):
        # Check for empty/commented lines
        if line and not line.startswith('#') and len(line.strip()) > 5:
            urls.append(line.strip())
    return urls

url = read_urls('urls.txt')


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
            print 'Guzzler started for %d seconds' % int(sys.argv[1][0:-1])
        except ValueError:
            pass
    elif sys.argv[1][-1] == 'm' or sys.argv[1][-1] == 'M':
        try:
            time_bound = True
            time_limit = int(sys.argv[1][0:-1]) * 60
            print 'Guzzler started for %d minutes' % int(sys.argv[1][0:-1])
        except ValueError:
            pass
    elif sys.argv[1][-1] == 'h' or sys.argv[1][-1] == 'H':
        try:
            time_bound = True
            time_limit = int(sys.argv[1][0:-1]) * 60 * 60
            print 'Guzzler started for %d hours' % int(sys.argv[1][0:-1])
        except ValueError:
            pass
    elif sys.argv[1][-1] == 'd' or sys.argv[1][-1] == 'D':
        try:
            time_bound = True
            time_limit = int(sys.argv[1][0:-1]) * 60 * 60 * 24
            print 'Guzzler started for %d days' % int(sys.argv[1][0:-1])
        except ValueError:
            pass
    elif sys.argv[1][-1] == 'b' or sys.argv[1][-1] == 'B':
        if sys.argv[1][-2] == 'm' or sys.argv[1][-2] == 'M':
            try:
                data_bound = True
                data_limit = int(sys.argv[1][0:-2])
                print 'Guzzler started for %d megabytes' % int(sys.argv[1][0:-2])
            except ValueError:
                pass
        elif sys.argv[1][-2] == 'G' or sys.argv[1][-2] == 'G':
            try:
                data_bound = True
                data_limit = int(sys.argv[1][0:-2]) * 1024
                print 'Guzzler started for %d gigabytes' % int(sys.argv[1][0:-2])
            except ValueError:
                pass
        elif sys.argv[1][-2] == 't' or sys.argv[1][-2] == 'T':
            try:
                data_bound = True
                data_limit = int(sys.argv[1][0:-2]) * 1024 * 1024
                print 'Guzzler started for %d terabytes' % int(sys.argv[1][0:-2])
            except ValueError:
                pass
    else:
        try:
            if int(sys.argv[1]) > 0:
                rounds = int(sys.argv[1])
                print 'Guzzler started for %d rounds' % int(sys.argv[1])
        except ValueError:
            pass

start_time = time.time()

each_data = []
total_data = Value(c_ulong, 0)


def guzzle(fileurl):
    semaphore = 0
    global not_enough, data_limit, data_bound, time_bound, time_limit, rounds, start_time, total_data
    #each_data[multiprocessing.current_process().name] = 0
    while not_enough:
        try:
            u = urllib2.urlopen(fileurl)
        except urllib2.URLError:
            print '\rInternet problems, bro',
            continue

        meta = u.info()
        file_size = int(meta.getheaders("Content-Length")[0])

        file_size_dl = 0
        block_sz = 1024 * 1024
        while True:
            buffer = u.read(block_sz)
            if not buffer:
                break

            file_size_dl += len(buffer)
            current_guzzled = (semaphore * (float(file_size) / (1024 * 1024))) + (
                file_size_dl / (1024 * 1024))
            #each_data[multiprocessing.current_process().name] += (file_size_dl/(1024*1024))
            total_data.value += len(buffer) / 1024 / 1024  # file_size_dl/1024/1024
            # print total_data,
            # print guzzle_status,

            # print multiprocessing.current_process().name, total_data.value, file_size_dl/1024/1024, file_size/1024/1024
            # print each_data
            if data_bound:
                if current_guzzled > data_limit:
                    not_enough = False
                    break  # sys.exit(0)

            if time_bound:
                if time.time() - start_time > time_limit:
                    not_enough = False
                    break  # sys.exit(0)

        semaphore += 1

        if not time_bound:
            if semaphore >= rounds:
                not_enough = False  # that is, enough is enough.

p = Pool(2)
workers = p.map_async(guzzle, url)

p.close()

while not workers.ready():
    # print total_data.value
    guzzle_status = "\r%d mb guzzled in %.2f minutes with an average speed of %.2fMB/s." % (
        total_data.value, ((time.time() - start_time) / 60), total_data.value / (((time.time() - start_time) / 60)) / 60)
    print guzzle_status,

p.join()

# print "Out!"
# guzzle('http://care.dlservice.microsoft.com/dl/download/2/9/C/29CC45EF-4CDA-4710-9FB3-1489786570A1/OfficeProfessionalPlus_x64_en-us.img')
