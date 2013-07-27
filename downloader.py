import urllib2, sys, time

#MS Office
url = "http://care.dlservice.microsoft.com/dl/download/2/9/C/29CC45EF-4CDA-4710-9FB3-1489786570A1/OfficeProfessionalPlus_x64_en-us.img"

#Chrome
#url = 'https://dl.google.com/dl/linux/direct/google-chrome-unstable_current_x86_64.rpm'

#test
#url = "http://download.thinkbroadband.com/10MB.zip" # testing

time_bound = False
time_limit = 0

data_bound = False
data_limit = 0

not_enough = True
rounds = 1000

if len(sys.argv)>1:
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
			if int(sys.argv[1])>0:
				rounds = int(sys.argv[1])
				print 'Guzzler started for %d rounds' % int(sys.argv[1])
		except ValueError:
			pass


file_name = url.split('/')[-1]
#guzzled_mb = 0.;
start_time = time.time()
semaphore = 0

while not_enough:
	
	try:
		u = urllib2.urlopen(url)
	except urllib2.URLError:
		print '\rInternet problems, bro',
		continue

	meta = u.info()
	file_size = int(meta.getheaders("Content-Length")[0])
	
	file_size_dl = 0
	block_sz = 1024*1
	while True:
	    buffer = u.read(block_sz)
	    if not buffer:
	        break

	    file_size_dl += len(buffer)
	    current_guzzled = (semaphore*(float(file_size)/(1024*1024)))+(file_size_dl/(1024*1024))
	    elapsed_time = ((time.time()-start_time)/60)

	    guzzle_status = "\r%d mb guzzled in %.2f minutes with an average speed of %.2fMB/s." % (current_guzzled, elapsed_time, current_guzzled/elapsed_time/60)

	    print guzzle_status,

	    if data_bound:
	    	if current_guzzled > data_limit:
	    		sys.exit(0)

	    if time_bound:
	    	if time.time()-start_time > time_limit:
				sys.exit(0)

	semaphore+=1

	if not time_bound:
		if semaphore >= rounds:
			not_enough = False #that is, enough is enough.